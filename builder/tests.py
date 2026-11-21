from io import StringIO
from types import SimpleNamespace

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from builder import rules
from goods.models import Case, Category, CoolingSystem


def cpu(socket='LGA 1700', tdp=125):
    return SimpleNamespace(socket=socket, thermal_design_power=tdp)


def board(socket='LGA 1700', form_factor='ATX', memory_type='DDR5'):
    return SimpleNamespace(socket=socket, form_factor=form_factor, memory_type=memory_type)


def ram(type_='DDR5'):
    return SimpleNamespace(type=type_)


def case(form_factor='ATX mid-tower'):
    return SimpleNamespace(form_factor=form_factor)


def cooler(compatibility='Intel LGA 1700, 1200; AMD AM4, AM5'):
    return SimpleNamespace(compatibility=compatibility)


def psu(power=850):
    return SimpleNamespace(power=power)


def gpu(connector='8-pin x 2'):
    return SimpleNamespace(power_connector=connector)


class HelpersTests(SimpleTestCase):
    def test_normalize(self):
        self.assertEqual(rules.normalize('LGA 1700'), rules.normalize('lga-1700'))
        self.assertEqual(rules.normalize('LGA 1700'), 'LGA1700')

    def test_cooling_sockets(self):
        self.assertEqual(
            rules.cooling_sockets('Intel LGA 1700, 1200, 1150; AMD AM4, AM5'),
            {'LGA1700', 'LGA1200', 'LGA1150', 'AM4', 'AM5'},
        )
        self.assertEqual(rules.cooling_sockets('universal'), set())

    def test_gpu_power(self):
        self.assertEqual(rules.gpu_power(gpu('8-pin x 2')), 300)
        self.assertEqual(rules.gpu_power(gpu('6-pin x 1, 8-pin x 1')), 225)
        self.assertEqual(rules.gpu_power(gpu('16-pin x 1')), 450)
        self.assertEqual(rules.gpu_power(gpu('none')), rules.UNKNOWN_GPU_W)

    def test_form_factor_aliases(self):
        self.assertEqual(rules.board_form_factor('Micro ATX'), rules.board_form_factor('mATX'))
        self.assertIsNone(rules.board_form_factor('Weird'))


class RuleTests(SimpleTestCase):
    def messages(self, parts):
        return [problem.message for problem in rules.find_problems(parts)]

    def test_empty_and_partial_builds_have_no_problems(self):
        self.assertEqual(self.messages({}), [])
        self.assertEqual(self.messages({'cpu': cpu()}), [])  # no motherboard yet

    def test_socket(self):
        self.assertEqual(self.messages({'cpu': cpu('LGA 1700'), 'motherboard': board('LGA1700')}), [])
        problems = rules.find_problems({'cpu': cpu('AM4'), 'motherboard': board('LGA 1700')})
        self.assertEqual(len(problems), 1)
        self.assertEqual(problems[0].slots, ('cpu', 'motherboard'))

    def test_memory(self):
        self.assertEqual(self.messages({'ram': ram('DDR5'), 'motherboard': board(memory_type='DDR5')}), [])
        self.assertEqual(len(self.messages({'ram': ram('DDR4'), 'motherboard': board(memory_type='DDR5')})), 1)

    def test_case(self):
        for case_type, board_type, fits in [
            ('ATX mid-tower', 'ATX', True),
            ('ATX mid-tower', 'Micro ATX', True),
            ('Compact tower', 'ATX', False),
            ('Compact tower', 'Micro ATX', True),
            ('Mini-ITX', 'Micro ATX', False),
            ('Mini-ITX', 'Mini-ITX', True),
        ]:
            with self.subTest(case=case_type, board=board_type):
                result = self.messages({'motherboard': board(form_factor=board_type), 'case': case(case_type)})
                self.assertEqual(result == [], fits)

    def test_unknown_case_is_a_problem(self):
        self.assertEqual(len(self.messages({'motherboard': board(), 'case': case('Cube')})), 1)

    def test_cooling(self):
        self.assertEqual(self.messages({'cpu': cpu('LGA 1700'), 'cooling': cooler()}), [])
        self.assertEqual(len(self.messages({'cpu': cpu('sWRX8'), 'cooling': cooler()})), 1)

    def test_power(self):
        # 125 + 300 + 150 = 575 W, with the margin 690 W
        parts = {'cpu': cpu(tdp=125), 'gpu': gpu('8-pin x 2')}
        self.assertEqual(self.messages({**parts, 'psu': psu(750)}), [])
        problems = rules.find_problems({**parts, 'psu': psu(650)})
        self.assertEqual(len(problems), 1)
        self.assertIn('690', problems[0].message)
        self.assertEqual(problems[0].slots, ('psu', 'cpu', 'gpu'))

    def test_power_without_cpu_and_gpu_uses_the_base_load(self):
        self.assertEqual(self.messages({'psu': psu(200)}), [])  # 150 * 1.2 = 180
        self.assertEqual(len(self.messages({'psu': psu(150)})), 1)


class CandidateTests(SimpleTestCase):
    def test_fitting_candidate_has_no_reasons(self):
        parts = {'motherboard': board('LGA 1700')}
        self.assertEqual(rules.check_candidate('cpu', cpu('LGA 1700'), parts), [])

    def test_not_fitting_candidate_has_a_reason(self):
        parts = {'motherboard': board('LGA 1700')}
        reasons = rules.check_candidate('cpu', cpu('AM4'), parts)
        self.assertEqual(len(reasons), 1)
        self.assertIn('AM4', reasons[0])

    def test_the_current_part_of_the_slot_is_replaced(self):
        # the build has an AM4 processor, but we try an LGA 1700 one for the same slot
        parts = {'motherboard': board('LGA 1700'), 'cpu': cpu('AM4')}
        self.assertEqual(rules.check_candidate('cpu', cpu('LGA 1700'), parts), [])

    def test_old_problems_of_other_parts_are_not_blamed_on_the_candidate(self):
        parts = {'motherboard': board('LGA 1700'), 'cpu': cpu('AM4')}  # already broken
        self.assertEqual(rules.check_candidate('ram', ram('DDR5'), parts), [])

    def test_a_weak_power_supply_is_rejected_for_a_hungry_cpu(self):
        parts = {'psu': psu(400), 'gpu': gpu('8-pin x 2')}
        self.assertEqual(len(rules.check_candidate('cpu', cpu(tdp=280), parts)), 1)


class CheckBuilderDataTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Category.objects.create(name='Cases', slug='cases', model_name='Case')

    def make_case(self, form_factor):
        return Case.objects.create(
            name='Case ' + form_factor, slug='case-' + form_factor.replace(' ', '-'),
            manufacturer='Acme', price=50, quantity=1, category=self.category,
            form_factor=form_factor, material='Steel', front_panel_ports='USB',
            expansion_slots=7, drive_bays=2, cooling_system='Fans', dimensions='1 x 1 x 1 mm',
        )

    def test_good_data_passes(self):
        self.make_case('ATX mid-tower')
        out = StringIO()
        call_command('check_builder_data', stdout=out)
        self.assertIn('All products are understood', out.getvalue())

    def test_unknown_case_type_is_reported(self):
        self.make_case('Cube')
        with self.assertRaises(CommandError) as context:
            call_command('check_builder_data')
        self.assertIn('Cube', str(context.exception))

    def test_cooler_without_sockets_is_reported(self):
        CoolingSystem.objects.create(
            name='Cooler', slug='cooler', manufacturer='Acme', price=10, quantity=1, category=self.category,
            type='Air', fan_size=120, bearing_type='x', airflow=1, noise_level=1, dimensions='1 mm',
            compatibility='universal',
        )
        with self.assertRaises(CommandError) as context:
            call_command('check_builder_data')
        self.assertIn('Cooler', str(context.exception))
