from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from usuarios.models import Usuario

from .models import Multa


class CrearMultaTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Cajero")
        self.usuario = Usuario.objects.create_user(
            username="cajero",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

        sector = Sector.objects.create(nombre="Sector A")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta A")
        self.abonado = Abonado.objects.create(
            codigo="AB001",
            cedula_ruc="0101010101",
            nombres="Ana",
            apellidos="Agua",
            direccion="Calle 1",
            sector=sector,
            ruta=ruta,
        )

    def datos_multa(self, **overrides):
        datos = {
            "abonado": self.abonado.id,
            "tipo": "OTRA",
            "motivo": "Prueba de multa",
            "fecha": date(2026, 6, 1).isoformat(),
            "valor": "10.00",
        }
        datos.update(overrides)
        return datos

    def test_rechaza_valor_no_numerico_sin_crear_multa(self):
        response = self.client.post(
            reverse("multas:crear"),
            self.datos_multa(valor="abc"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise los datos ingresados.")
        self.assertEqual(Multa.objects.count(), 0)

    def test_rechaza_valor_cero_sin_crear_multa(self):
        response = self.client.post(
            reverse("multas:crear"),
            self.datos_multa(valor="0"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "El valor de la multa debe ser mayor a cero.",
        )
        self.assertEqual(Multa.objects.count(), 0)

    def test_rechaza_tipo_no_permitido_sin_crear_multa(self):
        response = self.client.post(
            reverse("multas:crear"),
            self.datos_multa(tipo="TIPO_INVALIDO"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise los datos ingresados.")
        self.assertEqual(Multa.objects.count(), 0)

    def test_creacion_valida_registra_multa(self):
        response = self.client.post(
            reverse("multas:crear"),
            self.datos_multa(valor="25.50"),
        )

        self.assertRedirects(response, reverse("multas:lista"))

        multa = Multa.objects.get()
        self.assertEqual(multa.abonado, self.abonado)
        self.assertEqual(multa.tipo, "OTRA")
        self.assertEqual(multa.valor, Decimal("25.50"))
        self.assertEqual(multa.creado_por, self.usuario)
        self.assertEqual(multa.actualizado_por, self.usuario)

    def test_put_crear_multa_no_esta_permitido(self):
        response = self.client.put(
            reverse("multas:crear"),
            data=self.datos_multa(valor="25.50"),
        )

        self.assertEqual(response.status_code, 405)


class ExportarReporteMultasPermisosTests(TestCase):
    def crear_usuario(self, rol):
        grupo = Group.objects.create(name=rol)
        usuario = Usuario.objects.create_user(
            username=f"{rol.lower()}_export",
            password="clave-segura",
        )
        usuario.groups.add(grupo)
        return usuario

    def test_cajero_no_puede_exportar_reporte_multas_excel(self):
        self.client.force_login(self.crear_usuario("Cajero"))

        response = self.client.get(reverse("multas:reporte_excel"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))


class AnularMultaTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin_multas",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

        sector = Sector.objects.create(nombre="Sector Multa")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta Multa")
        abonado = Abonado.objects.create(
            codigo="AB-MUL",
            cedula_ruc="0505050505",
            nombres="Multa",
            apellidos="Prueba",
            direccion="Calle Multa",
            sector=sector,
            ruta=ruta,
        )
        self.multa = Multa.objects.create(
            abonado=abonado,
            tipo="OTRA",
            motivo="Multa de prueba",
            fecha=date(2026, 6, 1),
            valor=Decimal("15.00"),
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def test_get_muestra_confirmacion_sin_anular(self):
        response = self.client.get(
            reverse("multas:anular", args=[self.multa.id])
        )

        self.assertEqual(response.status_code, 200)
        self.multa.refresh_from_db()
        self.assertEqual(self.multa.estado, "PENDIENTE")

    def test_post_sin_motivo_no_anula(self):
        response = self.client.post(
            reverse("multas:anular", args=[self.multa.id]),
            {"motivo": ""},
        )

        self.assertRedirects(
            response,
            reverse("multas:anular", args=[self.multa.id]),
        )
        self.multa.refresh_from_db()
        self.assertEqual(self.multa.estado, "PENDIENTE")

    def test_post_con_motivo_anula_multa(self):
        response = self.client.post(
            reverse("multas:anular", args=[self.multa.id]),
            {"motivo": "Registro duplicado"},
        )

        self.assertRedirects(response, reverse("multas:lista"))
        self.multa.refresh_from_db()
        self.assertEqual(self.multa.estado, "ANULADA")
        self.assertEqual(self.multa.motivo_anulacion, "Registro duplicado")

    def test_put_no_esta_permitido(self):
        response = self.client.put(
            reverse("multas:anular", args=[self.multa.id]),
            data={"motivo": "No permitido"},
        )

        self.assertEqual(response.status_code, 405)


class CobrarMultaTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Cajero")
        self.usuario = Usuario.objects.create_user(
            username="cajero_multa",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

        sector = Sector.objects.create(nombre="Sector Cobro Multa")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta Cobro Multa")
        abonado = Abonado.objects.create(
            codigo="AB-COB-MUL",
            cedula_ruc="0606060606",
            nombres="Cobro",
            apellidos="Multa",
            direccion="Calle Cobro",
            sector=sector,
            ruta=ruta,
        )
        self.multa = Multa.objects.create(
            abonado=abonado,
            tipo="OTRA",
            motivo="Multa pendiente",
            fecha=date(2026, 6, 1),
            valor=Decimal("12.00"),
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def test_put_cobrar_multa_no_esta_permitido(self):
        response = self.client.put(
            reverse("multas:cobrar", args=[self.multa.id]),
            data={"metodo_pago": "EFECTIVO"},
        )

        self.assertEqual(response.status_code, 405)
