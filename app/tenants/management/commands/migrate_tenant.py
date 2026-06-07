from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from tenants.database import configurar_base_tenant
from tenants.models import Tenant


class Command(BaseCommand):
    help = "Ejecuta migraciones operativas en la base de un tenant activo."

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

        alias = configurar_base_tenant(tenant)
        self.stdout.write(
            f"Migrando tenant {tenant.slug}: base {tenant.db_name} alias {alias}"
        )
        call_command(
            "migrate",
            database=alias,
            interactive=False,
            verbosity=options["verbosity"],
        )
        self.stdout.write(self.style.SUCCESS(f"Migraciones completadas: {tenant.slug}"))
