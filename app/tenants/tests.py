from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.admin.sites import AdminSite
from django.core.management import call_command
from django.db import router
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.urls import resolve
from usuarios.models import Usuario
from usuarios.context_processors import roles_usuario

from .context import activar_tenant_db, limpiar_tenant_db, obtener_tenant_db_alias
from .admin import TenantAdmin, TenantAdminPasswordResetForm
from .database import alias_para_tenant
from .management.commands.provisionar_tenant import Command as ProvisionarTenantCommand
from .middleware import TenantPathMiddleware
from .models import Tenant
from .modules import TENANT_MODULE_KEYS


class TenantModelTests(TestCase):
    databases = {"master"}

    @override_settings(TENANT_DB_PREFIX="sistema_agua_")
    def test_construye_db_name_desde_slug(self):
        tenant = Tenant.objects.create(
            slug="carabuela",
            nombre="Junta Carabuela",
        )

        self.assertEqual(tenant.db_name, "sistema_agua_carabuela")
        self.assertEqual(tenant.ruta_base, "/carabuela/")

    @override_settings(TENANT_DB_PREFIX="agua_")
    def test_respeta_db_name_manual(self):
        tenant = Tenant.objects.create(
            slug="esperanza",
            nombre="Junta Esperanza",
            db_name="tenant_personalizado",
        )

        self.assertEqual(tenant.db_name, "tenant_personalizado")

    def test_normaliza_slug_a_minusculas(self):
        tenant = Tenant.objects.create(
            slug="Pesillo",
            nombre="Junta Pesillo",
        )

        self.assertEqual(tenant.slug, "pesillo")

    def test_tenant_nuevo_habilita_todos_los_modulos_por_defecto(self):
        tenant = Tenant.objects.create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
        )

        self.assertEqual(tenant.modulos_habilitados, list(TENANT_MODULE_KEYS))

    def test_descarta_modulos_desconocidos(self):
        tenant = Tenant.objects.create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
            modulos_habilitados=["panel", "multas", "desconocido"],
        )

        self.assertEqual(tenant.modulos_habilitados, ["panel", "multas"])


class TenantAdminTests(TestCase):
    databases = {"default", "master"}

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = TenantAdmin(Tenant, AdminSite())

    def test_oculta_tenants_en_admin_de_un_tenant(self):
        request = self.factory.get("/rumipamba/admin/tenants/tenant/")
        request.tenant = object()

        self.assertFalse(self.admin.has_module_permission(request))
        self.assertFalse(self.admin.has_view_permission(request))
        self.assertFalse(self.admin.has_add_permission(request))
        self.assertFalse(self.admin.has_change_permission(request))
        self.assertFalse(self.admin.has_delete_permission(request))

    def test_permite_tenants_fuera_de_ruta_tenant(self):
        request = self.factory.get("/admin/tenants/tenant/")
        request.tenant = None
        request.user = type(
            "User",
            (),
            {
                "has_module_perms": lambda self, app_label: True,
                "has_perm": lambda self, perm: True,
            },
        )()

        self.assertTrue(self.admin.has_module_permission(request))
        self.assertTrue(self.admin.has_view_permission(request))

    def test_form_reset_admin_valida_confirmacion(self):
        form = TenantAdminPasswordResetForm(
            {
                "username": "admin_rumipamba",
                "password": "ClaveSegura123",
                "password_confirm": "OtraClave123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Las claves no coinciden.", form.errors["__all__"])

    @patch("tenants.admin.configurar_base_tenant")
    def test_reset_admin_password_actualiza_usuario_en_base_tenant(self, configurar_mock):
        configurar_mock.return_value = "default"
        tenant = Tenant.objects.using("master").create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
            db_name="sistema_agua_rumipamba",
        )
        usuario = Usuario.objects.db_manager("default").create_user(
            username="admin_rumipamba",
            password="ClaveAnterior123",
            is_staff=False,
            is_superuser=False,
        )
        usuario.save(using="default")
        request = self.factory.post(
            f"/admin/tenants/tenant/{tenant.pk}/reset-admin-password/",
            {
                "username": "admin_rumipamba",
                "password": "ClaveNueva123",
                "password_confirm": "ClaveNueva123",
            },
        )
        request.tenant = None
        request.user = type(
            "User",
            (),
            {
                "is_active": True,
                "is_staff": True,
                "is_superuser": True,
                "has_perm": lambda self, perm: True,
                "has_module_perms": lambda self, app_label: True,
            },
        )()
        request._messages = type(
            "Messages",
            (),
            {"add": lambda self, level, message, extra_tags="", fail_silently=False: None},
        )()

        response = self.admin.reset_admin_password_view(request, str(tenant.pk))
        usuario = Usuario.objects.using("default").get(username="admin_rumipamba")

        self.assertEqual(response.status_code, 302)
        self.assertTrue(usuario.check_password("ClaveNueva123"))
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)
        self.assertTrue(usuario.is_active)


class TenantCommandTests(TestCase):
    databases = {"default", "master"}

    def test_crear_tenant_registra_en_master(self):
        salida = StringIO()

        call_command(
            "crear_tenant",
            "carabuela",
            "Junta Carabuela",
            stdout=salida,
        )

        self.assertTrue(
            Tenant.objects.using("master").filter(slug="carabuela").exists()
        )
        self.assertIn("Tenant creado: carabuela", salida.getvalue())

    def test_listar_tenants_muestra_registros(self):
        Tenant.objects.using("master").create(
            slug="esperanza",
            nombre="Junta Esperanza",
            db_name="sistema_agua_esperanza",
        )
        salida = StringIO()

        call_command("listar_tenants", stdout=salida)

        self.assertIn(
            "esperanza | Junta Esperanza | sistema_agua_esperanza | activo",
            salida.getvalue(),
        )

    @patch("tenants.management.commands.crear_base_tenant.crear_base_datos_tenant")
    def test_crear_base_tenant_crea_base_fisica(self, crear_base_mock):
        crear_base_mock.return_value = True
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        salida = StringIO()

        call_command("crear_base_tenant", "carabuela", stdout=salida)

        crear_base_mock.assert_called_once_with("sistema_agua_carabuela")
        self.assertIn("Base tenant creada: sistema_agua_carabuela", salida.getvalue())

    @patch("tenants.management.commands.crear_base_tenant.crear_base_datos_tenant")
    def test_crear_base_tenant_informa_si_ya_existe(self, crear_base_mock):
        crear_base_mock.return_value = False
        Tenant.objects.using("master").create(
            slug="esperanza",
            nombre="Junta Esperanza",
            db_name="sistema_agua_esperanza",
        )
        salida = StringIO()

        call_command("crear_base_tenant", "esperanza", stdout=salida)

        self.assertIn(
            "La base tenant ya existe: sistema_agua_esperanza",
            salida.getvalue(),
        )

    def test_crear_base_tenant_rechaza_tenant_inactivo(self):
        Tenant.objects.using("master").create(
            slug="pesillo",
            nombre="Junta Pesillo",
            activo=False,
        )

        with self.assertRaisesMessage(Exception, "esta inactivo"):
            call_command("crear_base_tenant", "pesillo")

    @patch("tenants.management.commands.migrate_tenant.call_command")
    def test_migrate_tenant_configura_alias_y_ejecuta_migrate(self, migrate_mock):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        alias = alias_para_tenant("carabuela")
        self.addCleanup(settings.DATABASES.pop, alias, None)
        salida = StringIO()

        call_command("migrate_tenant", "carabuela", stdout=salida)

        self.assertEqual(settings.DATABASES[alias]["NAME"], "sistema_agua_carabuela")
        migrate_mock.assert_called_once_with(
            "migrate",
            database=alias,
            interactive=False,
            verbosity=1,
        )
        self.assertIn("Migraciones completadas: carabuela", salida.getvalue())

    def test_migrate_tenant_rechaza_tenant_inactivo(self):
        Tenant.objects.using("master").create(
            slug="pesillo",
            nombre="Junta Pesillo",
            activo=False,
        )

        with self.assertRaisesMessage(Exception, "esta inactivo"):
            call_command("migrate_tenant", "pesillo")

    @patch("tenants.management.commands.migrate_tenants.call_command")
    def test_migrate_tenants_migra_solo_activos(self, migrate_tenant_mock):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
        )
        Tenant.objects.using("master").create(
            slug="pesillo",
            nombre="Junta Pesillo",
            activo=False,
        )

        call_command("migrate_tenants")

        migrate_tenant_mock.assert_called_once()
        self.assertEqual(migrate_tenant_mock.call_args.args[:2], ("migrate_tenant", "carabuela"))

    @override_settings(TENANT_SLUGS=["carabuela"])
    @patch("tenants.management.commands.provisionar_tenant.Command._crear_admin")
    @patch("tenants.management.commands.provisionar_tenant.Command._crear_roles")
    @patch("tenants.management.commands.provisionar_tenant.Command._migrar_tenant")
    @patch("tenants.management.commands.provisionar_tenant.crear_base_datos_tenant")
    def test_provisionar_tenant_prepara_junta_completa(
        self,
        crear_base_mock,
        migrar_mock,
        crear_roles_mock,
        crear_admin_mock,
    ):
        crear_base_mock.return_value = True
        migrar_mock.return_value = "tenant_carabuela"
        salida = StringIO()

        call_command(
            "provisionar_tenant",
            "carabuela",
            "Junta Carabuela",
            "--admin-user",
            "admin_carabuela",
            "--admin-password",
            "ClaveSegura123",
            stdout=salida,
        )

        tenant = Tenant.objects.using("master").get(slug="carabuela")
        crear_base_mock.assert_called_once_with("sistema_agua_carabuela")
        migrar_mock.assert_called_once_with(tenant, 1)
        crear_roles_mock.assert_called_once_with("tenant_carabuela")
        crear_admin_mock.assert_called_once()
        self.assertIn("Tenant provisionado: carabuela", salida.getvalue())

    @override_settings(TENANT_SLUGS=["carabuela"])
    @patch("tenants.management.commands.provisionar_tenant.Command._crear_admin")
    @patch("tenants.management.commands.provisionar_tenant.Command._crear_roles")
    @patch("tenants.management.commands.provisionar_tenant.Command._migrar_tenant")
    @patch("tenants.management.commands.provisionar_tenant.crear_base_datos_tenant")
    def test_provisionar_tenant_advierte_si_slug_no_esta_en_env(
        self,
        crear_base_mock,
        migrar_mock,
        crear_roles_mock,
        crear_admin_mock,
    ):
        crear_base_mock.return_value = True
        migrar_mock.return_value = "tenant_san_pablo"
        salida = StringIO()

        call_command(
            "provisionar_tenant",
            "san-pablo",
            "Junta San Pablo",
            "--admin-user",
            "admin_san_pablo",
            "--admin-password",
            "ClaveSegura123",
            stdout=salida,
        )

        self.assertIn("agregue 'san-pablo' a TENANT_SLUGS", salida.getvalue())

    def test_provisionar_tenant_crea_admin_con_permiso_admin_django(self):
        grupo = Group.objects.using("default").create(name="Administrador")
        comando = ProvisionarTenantCommand()
        comando.stdout = StringIO()

        comando._crear_admin(
            "default",
            "admin_rumipamba",
            "ClaveSegura123",
            "admin@rumipamba.local",
            {"reset_admin_password": False},
        )

        usuario = Usuario.objects.using("default").get(username="admin_rumipamba")

        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.is_superuser)
        self.assertTrue(usuario.is_active)
        self.assertTrue(usuario.check_password("ClaveSegura123"))
        self.assertTrue(usuario.groups.filter(id=grupo.id).exists())


class TenantRouterTests(TestCase):
    databases = {"master"}

    def test_tenants_migran_solo_en_master(self):
        self.assertTrue(router.allow_migrate("master", "tenants"))
        self.assertFalse(router.allow_migrate("default", "tenants"))
        self.assertFalse(router.allow_migrate("master", "abonados"))

    def test_apps_operativas_usan_tenant_activo(self):
        token = activar_tenant_db("tenant_carabuela")

        try:
            self.assertEqual(router.db_for_read(Group), "tenant_carabuela")
            self.assertEqual(router.db_for_write(Group), "tenant_carabuela")
            self.assertTrue(router.allow_migrate("tenant_carabuela", "auth"))
            self.assertFalse(router.allow_migrate("tenant_carabuela", "tenants"))
        finally:
            limpiar_tenant_db(token)

    def test_apps_operativas_sin_tenant_usan_routing_normal(self):
        self.assertEqual(router.db_for_read(Group), "default")
        self.assertEqual(router.db_for_write(Group), "default")

    def test_tenant_path_middleware_va_antes_de_sesiones(self):
        self.assertLess(
            settings.MIDDLEWARE.index("tenants.middleware.TenantPathMiddleware"),
            settings.MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware"),
        )


class TenantPathMiddlewareTests(TestCase):
    databases = {"master"}

    def setUp(self):
        self.factory = RequestFactory()

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_detecta_tenant_y_reescribe_path_info(self):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        request = self.factory.get("/carabuela/panel/")

        middleware = TenantPathMiddleware(lambda req: HttpResponse(req.path_info))
        try:
            response = middleware(request)

            self.assertEqual(response.content.decode(), "/panel/")
            self.assertEqual(request.tenant_slug, "carabuela")
            self.assertEqual(request.tenant_db_alias, "tenant_carabuela")
            self.assertEqual(obtener_tenant_db_alias(), "")
            self.assertEqual(
                settings.DATABASES["tenant_carabuela"]["NAME"],
                "sistema_agua_carabuela",
            )
        finally:
            settings.DATABASES.pop("tenant_carabuela", None)

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_prefija_redirect_relativo_con_tenant(self):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        request = self.factory.get("/carabuela/login/")

        middleware = TenantPathMiddleware(lambda req: HttpResponseRedirect("/panel/"))
        try:
            response = middleware(request)

            self.assertEqual(response["Location"], "/carabuela/panel/")
        finally:
            settings.DATABASES.pop("tenant_carabuela", None)

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_no_duplica_prefijo_en_redirect_tenant(self):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        request = self.factory.get("/carabuela/login/")

        middleware = TenantPathMiddleware(
            lambda req: HttpResponseRedirect("/carabuela/panel/")
        )
        try:
            response = middleware(request)

            self.assertEqual(response["Location"], "/carabuela/panel/")
        finally:
            settings.DATABASES.pop("tenant_carabuela", None)

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_deja_ruta_legacy_sin_tenant(self):
        request = self.factory.get("/panel/")

        middleware = TenantPathMiddleware(lambda req: HttpResponse(req.path_info))
        response = middleware(request)

        self.assertEqual(response.content.decode(), "/panel/")
        self.assertIsNone(request.tenant)
        self.assertEqual(request.tenant_slug, "")
        self.assertEqual(obtener_tenant_db_alias(), "")

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_deja_redirect_legacy_sin_prefijo(self):
        request = self.factory.get("/login/")

        middleware = TenantPathMiddleware(lambda req: HttpResponseRedirect("/panel/"))
        response = middleware(request)

        self.assertEqual(response["Location"], "/panel/")

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_redirige_ruta_legacy_si_viene_desde_tenant(self):
        request = self.factory.get(
            "/abonados/?page=2",
            HTTP_REFERER="http://testserver/carabuela/panel/",
        )

        middleware = TenantPathMiddleware(lambda req: HttpResponse(req.path_info))
        response = middleware(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/carabuela/abonados/?page=2")

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_no_redirige_ruta_legacy_con_referer_externo(self):
        request = self.factory.get(
            "/abonados/",
            HTTP_REFERER="http://externo.test/carabuela/panel/",
        )

        middleware = TenantPathMiddleware(lambda req: HttpResponse(req.path_info))
        response = middleware(request)

        self.assertEqual(response.content.decode(), "/abonados/")

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_menu_base_usa_prefijo_tenant(self):
        request = self.factory.get("/carabuela/panel/")
        request.tenant_path_prefix = "/carabuela"

        html = render_to_string(
            "base/base.html",
            {
                "request": request,
                "puede_ver_panel": True,
                "puede_ver_abonados": True,
                "puede_ver_medidores": False,
                "puede_generar_lecturas": False,
                "puede_importar_lecturas": False,
                "puede_registrar_lecturas": False,
                "puede_generar_facturacion": False,
                "puede_ver_facturas": False,
                "puede_ver_reportes": False,
                "puede_ver_cartera": False,
                "puede_ver_suspensiones": False,
                "puede_ver_multas": False,
                "puede_ver_reporte_multas": False,
                "puede_administrar_sistema": False,
            },
        )

        self.assertIn('href="/carabuela/panel/"', html)
        self.assertIn('href="/carabuela/abonados/"', html)
        self.assertIn('action="/carabuela/logout/"', html)

    @override_settings(TENANT_SLUGS=["rumipamba"], TENANT_ROUTE_MODE="path")
    def test_bloquea_url_de_modulo_no_habilitado(self):
        tenant = Tenant.objects.using("master").create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
            db_name="sistema_agua_rumipamba",
            modulos_habilitados=["panel", "abonados"],
        )
        request = self.factory.get("/rumipamba/multas/")
        request.tenant = tenant
        request.path_info = "/multas/"
        request.resolver_match = resolve("/multas/")
        middleware = TenantPathMiddleware(lambda req: HttpResponse("ok"))

        response = middleware.process_view(request, None, (), {})

        self.assertEqual(response.status_code, 403)

    @override_settings(TENANT_SLUGS=["rumipamba"], TENANT_ROUTE_MODE="path")
    def test_permite_url_de_modulo_habilitado(self):
        tenant = Tenant.objects.using("master").create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
            db_name="sistema_agua_rumipamba",
            modulos_habilitados=["panel", "abonados"],
        )
        request = self.factory.get("/rumipamba/abonados/")
        request.tenant = tenant
        request.path_info = "/abonados/"
        request.resolver_match = resolve("/abonados/")
        middleware = TenantPathMiddleware(lambda req: HttpResponse("ok"))

        response = middleware.process_view(request, None, (), {})

        self.assertIsNone(response)


class TenantModuleContextTests(TestCase):
    databases = {"default", "master"}

    def setUp(self):
        self.factory = RequestFactory()
        self.grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin_rumipamba",
            password="ClaveSegura123",
            is_staff=True,
        )
        self.usuario.groups.add(self.grupo)

    def test_context_processor_oculta_permisos_de_modulo_no_habilitado(self):
        tenant = Tenant.objects.using("master").create(
            slug="rumipamba",
            nombre="Junta Rumipamba",
            modulos_habilitados=["panel", "abonados", "admin"],
        )
        request = self.factory.get("/rumipamba/panel/")
        request.user = self.usuario
        request.tenant = tenant

        contexto = roles_usuario(request)

        self.assertTrue(contexto["puede_ver_panel"])
        self.assertTrue(contexto["puede_ver_abonados"])
        self.assertFalse(contexto["puede_ver_multas"])
        self.assertFalse(contexto["puede_ver_suspensiones"])

    def test_menu_no_muestra_modulo_no_habilitado(self):
        request = self.factory.get("/rumipamba/panel/")
        request.tenant_path_prefix = "/rumipamba"

        html = render_to_string(
            "base/base.html",
            {
                "request": request,
                "puede_ver_panel": True,
                "puede_ver_abonados": True,
                "puede_ver_medidores": False,
                "puede_generar_lecturas": False,
                "puede_importar_lecturas": False,
                "puede_registrar_lecturas": False,
                "puede_generar_facturacion": False,
                "puede_ver_facturas": False,
                "puede_ver_reportes": False,
                "puede_ver_cartera": False,
                "puede_ver_suspensiones": False,
                "puede_ver_multas": False,
                "puede_ver_reporte_multas": False,
                "puede_administrar_sistema": False,
            },
        )

        self.assertIn('href="/rumipamba/abonados/"', html)
        self.assertNotIn('href="/rumipamba/multas/"', html)
        self.assertNotIn('href="/rumipamba/servicios/"', html)

    def test_tenant_url_prefija_enlaces_de_plantillas(self):
        request = self.factory.get("/carabuela/abonados/")
        request.tenant_path_prefix = "/carabuela"
        template = Template("{% tenant_url 'abonados:lista' %}")

        html = template.render(Context({"request": request}))

        self.assertEqual(html, "/carabuela/abonados/")

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_activa_contexto_tenant_durante_request(self):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            db_name="sistema_agua_carabuela",
        )
        request = self.factory.get("/carabuela/panel/")

        def responder(_request):
            self.assertEqual(obtener_tenant_db_alias(), "tenant_carabuela")
            self.assertEqual(router.db_for_read(Group), "tenant_carabuela")
            return HttpResponse("ok")

        middleware = TenantPathMiddleware(responder)
        response = middleware(request)

        self.assertEqual(response.content.decode(), "ok")
        self.assertEqual(obtener_tenant_db_alias(), "")

        settings.DATABASES.pop("tenant_carabuela", None)

    @override_settings(TENANT_SLUGS=["carabuela"], TENANT_ROUTE_MODE="path")
    def test_tenant_inactivo_responde_404(self):
        Tenant.objects.using("master").create(
            slug="carabuela",
            nombre="Junta Carabuela",
            activo=False,
        )
        request = self.factory.get("/carabuela/panel/")
        middleware = TenantPathMiddleware(lambda req: HttpResponse(req.path_info))

        with self.assertRaises(Http404):
            middleware(request)
