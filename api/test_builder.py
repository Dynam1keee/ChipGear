import json

from django.test import TestCase
from django.urls import reverse

from builder.models import Build
from carts.models import Cart
from goods import models as m
from users.models import User


def make(model, name, category, **fields):
    """Create a product of a model; the common fields have defaults."""
    common = {
        'manufacturer': 'Acme', 'price': 100, 'discount': 0, 'quantity': 5,
        'slug': name.lower().replace(' ', '-'),
    }
    common.update({k: fields.pop(k) for k in list(fields) if k in common})
    return model.objects.create(name=name, category=category, **common, **fields)


class BuilderTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        def category(name, model_name):
            return m.Category.objects.create(name=name, slug=name.lower().replace(' ', '-'), model_name=model_name)

        cats = {key: category(*args) for key, args in {
            'cpu': ('Processors', 'CPU'), 'board': ('Motherboards', 'motherboard'), 'ram': ('RAM', 'ram'),
            'gpu': ('Graphics cards', 'graphicscard'), 'psu': ('Power supplies', 'powersupply'),
            'case': ('Cases', 'case'), 'cooling': ('Cooling systems', 'coolingsystem'),
        }.items()}

        cpu = dict(cores=6, threads=12, base_clock=3.5, boost_clock=4.5, cache='20 MB', lithography='7 nm')
        board = dict(chipset='X', memory_slots=4, max_memory='128 GB', expansion_slots=3,
                     storage_interfaces='M.2', rear_panel_ports='USB')
        ram = dict(capacity='16GB', speed=3200, modules=2, voltage=1.35, latency='CL16', dimensions='1 mm')
        case = dict(material='Steel', front_panel_ports='USB', expansion_slots=7, drive_bays=2,
                    cooling_system='Fans', dimensions='1 mm')
        psu = dict(efficiency=80, form_factor='ATX', fan_size='120', connectors='x', protections='x',
                   dimensions='1 mm', certification='Gold')

        cls.intel = make(m.CPU, 'Intel CPU', cats['cpu'], socket='LGA 1700', thermal_design_power=125, price=200, discount=10, **cpu)
        cls.amd = make(m.CPU, 'AMD CPU', cats['cpu'], socket='AM4', thermal_design_power=65, **cpu)
        cls.board_intel = make(m.Motherboard, 'Intel Board', cats['board'], socket='LGA 1700', form_factor='ATX', memory_type='DDR5', **board)
        cls.board_amd = make(m.Motherboard, 'AMD Board', cats['board'], socket='AM4', form_factor='Micro ATX', memory_type='DDR4', **board)
        cls.ram5 = make(m.RAM, 'DDR5 Kit', cats['ram'], type='DDR5', **ram)
        cls.ram4 = make(m.RAM, 'DDR4 Kit', cats['ram'], type='DDR4', **ram)
        cls.case_mid = make(m.Case, 'Mid Case', cats['case'], form_factor='ATX mid-tower', **case)
        cls.case_mini = make(m.Case, 'Mini Case', cats['case'], form_factor='Mini-ITX', **case)
        cls.psu_850 = make(m.PowerSupply, 'PSU 850', cats['psu'], power=850, **psu)
        cls.psu_400 = make(m.PowerSupply, 'PSU 400', cats['psu'], power=400, **psu)
        cls.cooler = make(m.CoolingSystem, 'Air Cooler', cats['cooling'], type='Air', fan_size=120, bearing_type='x', airflow=1,
                          noise_level=1, dimensions='1 mm', compatibility='Intel LGA 1700, 1200; AMD AM4, AM5')
        cls.radiator = make(m.CoolingSystem, 'Radiator', cats['cooling'], type='Liquid', fan_size=120, bearing_type='x', airflow=1,
                            noise_level=1, dimensions='1 mm', compatibility='Custom loops')
        cls.gpu = make(m.GraphicsCard, 'GPU', cats['gpu'], chipset='X', memory='8GB', memory_type='GDDR6', memory_bus=256,
                       core_clock=1500, boost_clock=1800, cuda_cores=3000, interfaces='HDMI', power_connector='8-pin x 2', dimensions='1 mm')
        cls.sold_out = make(m.CPU, 'Sold Out CPU', cats['cpu'], socket='LGA 1700', thermal_design_power=65, quantity=0, **cpu)

        cls.alice = User.objects.create_user(username='alice', password='pass12345')
        cls.bob = User.objects.create_user(username='bob', password='pass12345')

    def setUp(self):
        self.client.force_login(self.alice)

    def get(self):
        return self.client.get(reverse('api:builder'))

    def put(self, slot, product):
        return self.client.put(
            reverse('api:builder_slot', args=[slot]),
            data=json.dumps({'product_id': product.id}), content_type='application/json',
        )

    def put_all(self, *pairs):
        for slot, product in pairs:
            self.assertEqual(self.put(slot, product).status_code, 200, slot)


class BuildTests(BuilderTestCase):
    def test_guests_cannot_use_the_builder(self):
        self.client.logout()
        self.assertEqual(self.get().status_code, 403)
        self.assertEqual(self.put('cpu', self.intel).status_code, 403)
        self.assertEqual(self.client.get(reverse('api:builder_options', args=['cpu'])).status_code, 403)
        self.assertEqual(self.client.post(reverse('api:builder_add_to_cart')).status_code, 403)

    def test_a_new_build_is_empty(self):
        data = self.get().json()

        self.assertEqual(set(data['slots']), {'cpu', 'motherboard', 'ram', 'gpu', 'storage', 'psu', 'case', 'cooling'})
        self.assertTrue(all(part is None for part in data['slots'].values()))
        self.assertEqual(data['problems'], [])
        self.assertEqual(data['total_price'], '0.00')
        self.assertIsNone(data['estimated_power'])

    def test_a_part_is_put_into_a_slot(self):
        response = self.put('cpu', self.intel)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['slots']['cpu']['name'], 'Intel CPU')
        self.assertEqual(data['total_price'], '180.00')  # 200 with 10% off
        self.assertEqual(Build.objects.get(user=self.alice).cpu_id, self.intel.id)

    def test_a_part_of_another_kind_is_not_found(self):
        self.assertEqual(self.put('cpu', self.board_intel).status_code, 404)
        self.assertEqual(self.put('motherboard', self.intel).status_code, 404)

    def test_unknown_slot_is_not_found(self):
        self.assertEqual(self.put('monitor', self.intel).status_code, 404)
        self.assertEqual(self.client.delete(reverse('api:builder_slot', args=['monitor'])).status_code, 404)

    def test_bad_product_id(self):
        response = self.client.put(reverse('api:builder_slot', args=['cpu']), data=json.dumps({'product_id': 'x'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)

    def test_a_part_that_does_not_fit_is_rejected_with_reasons(self):
        self.put_all(('motherboard', self.board_intel))

        response = self.put('cpu', self.amd)

        self.assertEqual(response.status_code, 400)
        self.assertIn('AM4', response.json()['non_field_errors'][0])
        self.assertIsNone(Build.objects.get(user=self.alice).cpu)

    def test_a_part_out_of_stock_is_rejected(self):
        response = self.put('cpu', self.sold_out)

        self.assertEqual(response.status_code, 400)
        self.assertIn('out of stock', response.json()['non_field_errors'][0])

    def test_a_part_can_be_replaced(self):
        self.put_all(('cpu', self.intel), ('motherboard', self.board_intel))
        # the board does not fit the AMD processor, so first the board goes away
        self.assertEqual(self.put('cpu', self.amd).status_code, 400)
        self.client.delete(reverse('api:builder_slot', args=['motherboard']))

        self.assertEqual(self.put('cpu', self.amd).json()['slots']['cpu']['name'], 'AMD CPU')

    def test_a_slot_is_emptied(self):
        self.put_all(('cpu', self.intel))

        response = self.client.delete(reverse('api:builder_slot', args=['cpu']))

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()['slots']['cpu'])

    def test_the_whole_build_is_cleared(self):
        self.put_all(('cpu', self.intel), ('motherboard', self.board_intel))

        response = self.client.delete(reverse('api:builder'))

        self.assertTrue(all(part is None for part in response.json()['slots'].values()))

    def test_a_full_build_and_its_power(self):
        self.put_all(
            ('cpu', self.intel), ('motherboard', self.board_intel), ('ram', self.ram5), ('case', self.case_mid),
            ('cooling', self.cooler), ('gpu', self.gpu), ('psu', self.psu_850),
        )

        data = self.get().json()

        self.assertEqual(data['problems'], [])
        self.assertEqual(data['estimated_power'], 575)  # 125 + 300 + 150
        self.assertEqual(data['recommended_psu'], 690)

    def test_a_weak_power_supply_is_rejected(self):
        self.put_all(('cpu', self.intel), ('gpu', self.gpu))

        response = self.put('psu', self.psu_400)

        self.assertEqual(response.status_code, 400)
        self.assertIn('690', response.json()['non_field_errors'][0])

    def test_builds_of_users_are_separate(self):
        self.put_all(('cpu', self.intel))
        self.client.force_login(self.bob)

        self.assertIsNone(self.get().json()['slots']['cpu'])

    def test_a_deleted_product_empties_the_slot(self):
        self.put_all(('cpu', self.intel))

        m.Product.objects.filter(id=self.intel.id).delete()

        self.assertIsNone(self.get().json()['slots']['cpu'])


class OptionsTests(BuilderTestCase):
    def options(self, slot, query=''):
        return self.client.get(reverse('api:builder_options', args=[slot]) + query).json()

    def test_all_parts_of_the_kind_are_listed(self):
        options = self.options('cpu')

        self.assertEqual({o['name'] for o in options}, {'Intel CPU', 'AMD CPU', 'Sold Out CPU'})
        self.assertTrue(all(o['reasons'] == [] for o in options if o['name'] != 'Sold Out CPU'))

    def test_options_know_what_does_not_fit(self):
        self.put_all(('motherboard', self.board_intel))

        by_name = {o['name']: o for o in self.options('cpu')}

        self.assertTrue(by_name['Intel CPU']['compatible'])
        self.assertFalse(by_name['AMD CPU']['compatible'])
        self.assertIn('AM4', by_name['AMD CPU']['reasons'][0])
        self.assertFalse(by_name['Sold Out CPU']['compatible'])

    def test_only_compatible(self):
        self.put_all(('motherboard', self.board_intel))

        names = {o['name'] for o in self.options('cpu', '?only_compatible=true')}

        self.assertEqual(names, {'Intel CPU'})

    def test_memory_and_cases_follow_the_motherboard(self):
        self.put_all(('motherboard', self.board_amd))

        self.assertEqual({o['name'] for o in self.options('ram', '?only_compatible=1')}, {'DDR4 Kit'})
        self.assertEqual({o['name'] for o in self.options('case', '?only_compatible=1')}, {'Mid Case'})  # the Mini-ITX case is too small for Micro ATX

    def test_a_water_loop_part_is_never_a_cooler(self):
        by_name = {o['name']: o for o in self.options('cooling')}

        self.assertTrue(by_name['Air Cooler']['compatible'])
        self.assertFalse(by_name['Radiator']['compatible'])

    def test_unknown_slot(self):
        self.assertEqual(self.client.get(reverse('api:builder_options', args=['monitor'])).status_code, 404)


class AddToCartTests(BuilderTestCase):
    def add(self):
        return self.client.post(reverse('api:builder_add_to_cart'))

    def test_an_empty_build_cannot_be_bought(self):
        self.assertEqual(self.add().status_code, 400)

    def test_a_build_with_problems_cannot_be_bought(self):
        # the API would not allow this pair, so the build is made in the database
        Build.objects.create(user=self.alice, cpu=self.intel, motherboard=self.board_amd)

        response = self.add()

        self.assertEqual(response.status_code, 400)
        self.assertFalse(Cart.objects.filter(user=self.alice).exists())

    def test_the_parts_go_to_the_cart(self):
        self.put_all(('cpu', self.intel), ('motherboard', self.board_intel), ('ram', self.ram5))

        response = self.add()

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['total_quantity'], 3)
        self.assertEqual(data['total_price'], '380.00')  # 180 + 100 + 100
        self.assertEqual(Cart.objects.filter(user=self.alice).count(), 3)

    def test_adding_twice_increases_quantities_but_not_above_stock(self):
        self.put_all(('cpu', self.intel))
        m.Product.objects.filter(id=self.intel.id).update(quantity=1)
        self.assertEqual(self.add().status_code, 200)

        response = self.add()

        self.assertEqual(response.status_code, 400)
        self.assertIn('Intel CPU', response.json()['non_field_errors'][0])
        self.assertEqual(Cart.objects.get(user=self.alice).quantity, 1)
