from django.core.management import call_command
from django.core.management.base import BaseCommand

from tenants.models import Tenant


class Command(BaseCommand):
    help = "Ejecuta migraciones operativas en todos los tenants activos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--include-inactive",
            action="store_true",
            help="Incluye tenants inactivos.",
        )

    def handle(self, *args, **options):
        tenants = Tenant.objects.using("master").order_by("nombre")

        if not options["include_inactive"]:
            tenants = tenants.filter(activo=True)

        if not tenants.exists():
            self.stdout.write("No existen tenants para migrar.")
            return

        for tenant in tenants:
            call_command(
                "migrate_tenant",
                tenant.slug,
                verbosity=options["verbosity"],
                stdout=self.stdout,
            )
