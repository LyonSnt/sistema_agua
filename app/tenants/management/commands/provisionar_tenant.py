from django.conf import settings
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from tenants.database import configurar_base_tenant, crear_base_datos_tenant
from tenants.modules import parsear_modulos
from tenants.models import Tenant
from usuarios.models import Usuario


class Command(BaseCommand):
    help = "Crea y prepara una junta: tenant, base, migraciones, roles y admin inicial."

    roles = [
        "Administrador",
        "Cajero",
        "Lecturista",
        "Supervisor",
        "Consulta",
    ]

    def add_arguments(self, parser):
        parser.add_argument("slug")
        parser.add_argument("nombre")
        parser.add_argument(
            "--db-name",
            dest="db_name",
            default="",
            help="Nombre de base de datos. Si se omite, se usa TENANT_DB_PREFIX + slug.",
        )
        parser.add_argument(
            "--admin-user",
            dest="admin_user",
            required=True,
            help="Usuario administrador inicial del tenant.",
        )
        parser.add_argument(
            "--admin-password",
            dest="admin_password",
            required=True,
            help="Clave inicial del usuario administrador.",
        )
        parser.add_argument(
            "--admin-email",
            dest="admin_email",
            default="",
            help="Correo opcional del usuario administrador.",
        )
        parser.add_argument(
            "--reset-admin-password",
            action="store_true",
            help="Actualiza la clave si el usuario administrador ya existe.",
        )
        parser.add_argument(
            "--modules",
            dest="modules",
            default="",
            help="Lista separada por comas de modulos habilitados. Si se omite, se habilitan todos.",
        )

    def handle(self, *args, **options):
        slug = options["slug"].strip().lower()
        nombre = options["nombre"].strip()
        db_name = options["db_name"].strip()
        admin_user = options["admin_user"].strip()
        admin_password = options["admin_password"]
        admin_email = options["admin_email"].strip()
        modules = options["modules"].strip()

        if not slug:
            raise CommandError("El slug no puede estar vacio.")

        if not nombre:
            raise CommandError("El nombre no puede estar vacio.")

        if not admin_user:
            raise CommandError("El usuario administrador no puede estar vacio.")

        try:
            modulos_habilitados = parsear_modulos(modules)
        except ValueError as exc:
            raise CommandError(str(exc)) from exc

        tenant = self._obtener_o_crear_tenant(
            slug,
            nombre,
            db_name,
            modulos_habilitados,
        )
        self._advertir_si_slug_no_esta_en_env(slug)
        self._crear_base_fisica(tenant)
        alias = self._migrar_tenant(tenant, options["verbosity"])
        self._crear_roles(alias)
        self._crear_admin(alias, admin_user, admin_password, admin_email, options)

        self.stdout.write(
            self.style.SUCCESS(
                f"Tenant provisionado: {tenant.slug} | {tenant.nombre} | {tenant.db_name}"
            )
        )

    def _obtener_o_crear_tenant(self, slug, nombre, db_name, modulos_habilitados):
        try:
            tenant, creado = Tenant.objects.using("master").get_or_create(
                slug=slug,
                defaults={
                    "nombre": nombre,
                    "db_name": db_name,
                    "modulos_habilitados": modulos_habilitados,
                },
            )
        except IntegrityError as exc:
            raise CommandError(
                f"No se pudo crear el tenant '{slug}'. Revise slug/db_name duplicados."
            ) from exc

        if creado:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Tenant creado: {tenant.slug} | {tenant.nombre} | {tenant.db_name}"
                )
            )
            return tenant

        self.stdout.write(f"Tenant ya existe: {tenant.slug} | {tenant.db_name}")
        return tenant

    def _advertir_si_slug_no_esta_en_env(self, slug):
        if slug in settings.TENANT_SLUGS:
            return

        self.stdout.write(
            self.style.WARNING(
                f"Advertencia: agregue '{slug}' a TENANT_SLUGS en .env "
                "y recree el contenedor web para acceder por URL."
            )
        )

    def _crear_base_fisica(self, tenant):
        creada = crear_base_datos_tenant(tenant.db_name)

        if creada:
            self.stdout.write(self.style.SUCCESS(f"Base creada: {tenant.db_name}"))
            return

        self.stdout.write(f"Base ya existe: {tenant.db_name}")

    def _migrar_tenant(self, tenant, verbosity):
        alias = configurar_base_tenant(tenant)
        self.stdout.write(
            f"Migrando tenant {tenant.slug}: base {tenant.db_name} alias {alias}"
        )
        call_command(
            "migrate",
            database=alias,
            interactive=False,
            verbosity=verbosity,
        )
        self.stdout.write(self.style.SUCCESS(f"Migraciones completadas: {tenant.slug}"))
        return alias

    def _crear_roles(self, alias):
        for nombre in self.roles:
            Group.objects.using(alias).get_or_create(name=nombre)

        self.stdout.write(self.style.SUCCESS("Roles base creados."))

    def _crear_admin(self, alias, username, password, email, options):
        admin_group = Group.objects.using(alias).get(name="Administrador")
        usuario, creado = Usuario.objects.using(alias).get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        if creado or options["reset_admin_password"]:
            usuario.set_password(password)

        usuario.email = email or usuario.email
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.is_active = True
        usuario.save(using=alias)
        usuario.groups.add(admin_group)

        if creado:
            self.stdout.write(self.style.SUCCESS(f"Administrador creado: {username}"))
            return

        self.stdout.write(f"Administrador ya existe: {username}")
