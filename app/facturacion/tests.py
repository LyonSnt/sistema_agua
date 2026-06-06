from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from auditoria.models import Auditoria
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import Medidor
from usuarios.models import Usuario

from .models import Factura


class AnularFacturaTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin_facturacion",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

        sector = Sector.objects.create(nombre="Sector Factura")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta Factura")
        abonado = Abonado.objects.create(
            codigo="AB-FAC",
            cedula_ruc="0404040404",
            nombres="Factura",
            apellidos="Prueba",
            direccion="Calle Factura",
            sector=sector,
            ruta=ruta,
        )
        medidor = Medidor.objects.create(
            abonado=abonado,
            numero="MED-FAC",
            lectura_inicial=Decimal("0.00"),
        )
        periodo = PeriodoFacturacion.objects.create(
            nombre="Agosto 2026",
            anio=2026,
            mes=8,
            fecha_inicio=date(2026, 8, 1),
            fecha_fin=date(2026, 8, 31),
            estado="ABIERTO",
        )
        lectura = Lectura.objects.create(
            periodo=periodo,
            medidor=medidor,
            lectura_anterior=Decimal("0.00"),
            lectura_actual=Decimal("10.00"),
            lectura_registrada=True,
        )
        self.factura = Factura.objects.create(
            numero="FAC-ANULAR",
            abonado=abonado,
            periodo=periodo,
            lectura=lectura,
            subtotal=Decimal("30.00"),
            total=Decimal("30.00"),
            saldo_pendiente=Decimal("30.00"),
            estado="PENDIENTE",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def test_get_muestra_confirmacion_sin_anular(self):
        response = self.client.get(
            reverse("facturacion:anular", args=[self.factura.id])
        )

        self.assertEqual(response.status_code, 200)
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.estado, "PENDIENTE")

    def test_post_sin_motivo_no_anula(self):
        response = self.client.post(
            reverse("facturacion:anular", args=[self.factura.id]),
            {"motivo": ""},
        )

        self.assertRedirects(
            response,
            reverse("facturacion:anular", args=[self.factura.id]),
        )
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.estado, "PENDIENTE")

    def test_post_con_motivo_anula_factura(self):
        response = self.client.post(
            reverse("facturacion:anular", args=[self.factura.id]),
            {"motivo": "Factura emitida por error"},
        )

        self.assertRedirects(
            response,
            reverse("facturacion:detalle", args=[self.factura.id]),
        )
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.estado, "ANULADA")
        self.assertEqual(
            self.factura.motivo_anulacion,
            "Factura emitida por error",
        )
        self.assertTrue(
            Auditoria.objects.filter(
                accion="ANULAR_FACTURA",
                modulo="Facturación",
                objeto_id=str(self.factura.id),
            ).exists()
        )

    def test_put_no_esta_permitido(self):
        response = self.client.put(
            reverse("facturacion:anular", args=[self.factura.id]),
            data={"motivo": "No permitido"},
        )

        self.assertEqual(response.status_code, 405)

    def test_put_generar_facturacion_no_esta_permitido(self):
        response = self.client.put(reverse("facturacion:generar"))

        self.assertEqual(response.status_code, 405)

    def test_put_agregar_rubro_factura_no_esta_permitido(self):
        response = self.client.put(
            reverse("facturacion:agregar_rubro", args=[self.factura.id]),
            data={"rubro": "1"},
        )

        self.assertEqual(response.status_code, 405)

    def test_descarga_pdf_registra_auditoria(self):
        response = self.client.get(
            reverse("facturacion:pdf", args=[self.factura.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            Auditoria.objects.filter(
                accion="EXPORTAR_REPORTE",
                modulo="Facturación",
                objeto_id=str(self.factura.id),
            ).exists()
        )
