from django.core.management.base import BaseCommand

from tenants.models import Tenant


class Command(BaseCommand):
    help = "Lista los tenants registrados en la base master."

    def handle(self, *args, **options):
        tenants = Tenant.objects.using("master").order_by("nombre")

        if not tenants.exists():
            self.stdout.write("No existen tenants registrados.")
            return

        for tenant in tenants:
            estado = "activo" if tenant.activo else "inactivo"
            self.stdout.write(
                f"{tenant.slug} | {tenant.nombre} | {tenant.db_name} | {estado}"
            )
