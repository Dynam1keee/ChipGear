from django.core.management.base import BaseCommand, CommandError

from builder import rules
from goods import models


class Command(BaseCommand):
    help = (
        'Checks that the products have values that the PC builder understands '
        '(case types, form factors, cooler sockets, power connectors).'
    )

    def handle(self, *args, **options):
        problems = []

        for case in models.Case.objects.all():
            if rules.case_takes(case.form_factor) is None:
                problems.append(f'Case "{case.name}": unknown type "{case.form_factor}"')

        for board in models.Motherboard.objects.all():
            if rules.board_form_factor(board.form_factor) is None:
                problems.append(f'Motherboard "{board.name}": unknown form factor "{board.form_factor}"')

        for cooling in models.CoolingSystem.objects.all():
            if not rules.is_cpu_cooler(cooling):
                # Not an error: for example a radiator of a custom water loop
                self.stdout.write(f'Note: "{cooling.name}" has no sockets, so it is not offered as a cooler.')

        for gpu in models.GraphicsCard.objects.all():
            if 'pin' not in gpu.power_connector.lower():
                problems.append(f'Graphics card "{gpu.name}": unknown power connector "{gpu.power_connector}"')

        for ram in models.RAM.objects.all():
            if not rules.normalize(ram.type).startswith('DDR'):
                problems.append(f'Memory "{ram.name}": unknown type "{ram.type}"')

        if problems:
            raise CommandError('Found problems:\n' + '\n'.join(problems))
        self.stdout.write(self.style.SUCCESS('All products are understood by the builder.'))
