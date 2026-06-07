from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from tenants.models import Tenant


class Command(BaseCommand):
    help = "Crea un tenant en la base master. No crea la base fisica."

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument("nombre")
        parser.add_argument(
            "--db-name",
            dest="db_name",
            default="",
            help="Nombre de base de datos. Si se omite, se usa TENANT_DB_PREFIX + slug.",
        )

    def handle(self, *args, **options):
        slug = options["slug"].strip().lower()
        nombre = options["nombre"].strip()
        db_name = options["db_name"].strip()

        if not slug:
            raise CommandError("El slug no puede estar vacio.")

        if not nombre:
            raise CommandError("El nombre no puede estar vacio.")

        try:
            tenant = Tenant.objects.using("master").create(
                slug=slug,
                nombre=nombre,
                db_name=db_name,
            )
        except IntegrityError as exc:
            raise CommandError(
                f"No se pudo crear el tenant '{slug}'. Revise slug/db_name duplicados."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Tenant creado: {tenant.slug} | {tenant.nombre} | {tenant.db_name}"
            )
        )
