from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from auditoria.models import Auditoria
from usuarios.models import Usuario


class ExportarReportesPermisosTests(TestCase):
    def crear_usuario(self, rol):
        grupo = Group.objects.create(name=rol)
        usuario = Usuario.objects.create_user(
            username=rol.lower(),
            password="clave-segura",
        )
        usuario.groups.add(grupo)
        return usuario

    def assert_redirect_panel(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))

    def test_cajero_no_puede_exportar_recaudacion_diaria_excel(self):
        self.client.force_login(self.crear_usuario("Cajero"))

        response = self.client.get(
            reverse("reportes:recaudacion_diaria_excel")
        )

        self.assert_redirect_panel(response)

    def test_consulta_no_puede_exportar_recaudacion_mensual_excel(self):
        self.client.force_login(self.crear_usuario("Consulta"))

        response = self.client.get(
            reverse("reportes:recaudacion_mensual_excel")
        )

        self.assert_redirect_panel(response)

    def test_cajero_no_puede_exportar_cartera_vencida_excel(self):
        self.client.force_login(self.crear_usuario("Cajero"))

        response = self.client.get(
            reverse("reportes:cartera_vencida_excel")
        )

        self.assert_redirect_panel(response)


class ParametrosReportesTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin-reportes",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

    def test_cierre_diario_con_fecha_invalida_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:cierre_diario"),
            {"fecha": "fecha-invalida"},
        )

        self.assertEqual(response.status_code, 200)

    def test_cierre_diario_pdf_con_fecha_invalida_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:cierre_diario_pdf"),
            {"fecha": "2026-99-99"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_recaudacion_diaria_con_fecha_invalida_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:recaudacion_diaria"),
            {"fecha": "abc"},
        )

        self.assertEqual(response.status_code, 200)

    def test_exportar_recaudacion_diaria_con_fecha_invalida_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:recaudacion_diaria_excel"),
            {"fecha": "abc"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(
            Auditoria.objects.filter(
                accion="EXPORTAR_REPORTE",
                modulo="Reportes",
                descripcion__icontains="Exportó recaudación diaria",
            ).exists()
        )

    def test_recaudacion_mensual_con_periodo_invalido_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:recaudacion_mensual"),
            {"anio": "hola", "mes": "99"},
        )

        self.assertEqual(response.status_code, 200)

    def test_recaudacion_mensual_pdf_con_periodo_invalido_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:recaudacion_mensual_pdf"),
            {"anio": "2026", "mes": "99"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_exportar_recaudacion_mensual_con_periodo_invalido_no_genera_error(self):
        response = self.client.get(
            reverse("reportes:recaudacion_mensual_excel"),
            {"anio": "hola", "mes": "1"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
