from django.core.management.base import BaseCommand, CommandError
from django.db.utils import OperationalError, ProgrammingError

from tenants.database import crear_base_datos_tenant
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Crea la base fisica PostgreSQL asociada a un tenant activo."

    def add_arguments(self, parser):
        parser.add_argument("slug")

    def handle(self, *args, **options):
        slug = options["slug"].strip().lower()

        if not slug:
            raise CommandError("El slug no puede estar vacio.")

        try:
            tenant = Tenant.objects.using("master").get(slug=slug)
        except Tenant.DoesNotExist as exc:
            raise CommandError(f"No existe un tenant con slug '{slug}'.") from exc

        if not tenant.activo:
            raise CommandError(f"El tenant '{slug}' esta inactivo.")

        try:
            creada = crear_base_datos_tenant(tenant.db_name)
        except (OperationalError, ProgrammingError) as exc:
            raise CommandError(
                f"No se pudo crear la base '{tenant.db_name}'. "
                "Revise permisos del usuario PostgreSQL y TENANT_ADMIN_DB_NAME."
            ) from exc

        if creada:
            self.stdout.write(
                self.style.SUCCESS(f"Base tenant creada: {tenant.db_name}")
            )
            return

        self.stdout.write(f"La base tenant ya existe: {tenant.db_name}")
