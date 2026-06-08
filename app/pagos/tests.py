from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from facturacion.models import Factura
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import Medidor
from usuarios.models import Usuario

from .models import Pago


class CobrarFacturaTests(TestCase):
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
        abonado = Abonado.objects.create(
            codigo="AB001",
            cedula_ruc="0101010101",
            nombres="Ana",
            apellidos="Agua",
            direccion="Calle 1",
            sector=sector,
            ruta=ruta,
        )
        medidor = Medidor.objects.create(
            abonado=abonado,
            numero="MED001",
            lectura_inicial=Decimal("10.00"),
        )
        periodo = PeriodoFacturacion.objects.create(
            nombre="Junio 2026",
            anio=2026,
            mes=6,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30),
            estado="ABIERTO",
        )
        lectura = Lectura.objects.create(
            periodo=periodo,
            medidor=medidor,
            lectura_anterior=Decimal("10.00"),
            lectura_actual=Decimal("20.00"),
            lectura_registrada=True,
        )

        self.factura = Factura.objects.create(
            numero="FAC-TEST-001",
            abonado=abonado,
            periodo=periodo,
            lectura=lectura,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            saldo_pendiente=Decimal("100.00"),
            estado="PENDIENTE",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def post_pago(self, valor):
        return self.client.post(
            reverse("pagos:cobrar", args=[self.factura.id]),
            {
                "metodo_pago": "EFECTIVO",
                "valor_pagado": valor,
                "referencia": "",
                "observacion": "",
            },
        )

    def test_rechaza_valor_no_numerico_sin_crear_pago(self):
        response = self.post_pago("abc")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ingrese un valor de pago válido.")
        self.assertEqual(Pago.objects.count(), 0)

    def test_rechaza_valor_cero_sin_crear_pago(self):
        response = self.post_pago("0")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "El valor pagado debe ser mayor a cero.",
        )
        self.assertEqual(Pago.objects.count(), 0)

    def test_rechaza_pago_mayor_al_saldo_sin_crear_pago(self):
        response = self.post_pago("150.00")

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "El valor pagado no puede ser mayor al saldo pendiente",
        )
        self.assertEqual(Pago.objects.count(), 0)

    def test_pago_valido_crea_pago_y_actualiza_factura(self):
        response = self.post_pago("40.00")

        pago = Pago.objects.get()
        self.assertRedirects(
            response,
            reverse("pagos:pago_exitoso", args=[pago.id]),
        )
        self.assertEqual(pago.valor_pagado, Decimal("40.00"))

        self.factura.refresh_from_db()
        self.assertEqual(self.factura.total_pagado, Decimal("40.00"))
        self.assertEqual(self.factura.saldo_pendiente, Decimal("60.00"))
        self.assertEqual(self.factura.estado, "PARCIAL")

    def test_error_en_auditoria_revierte_pago_y_factura(self):
        with patch(
            "pagos.views.registrar_auditoria",
            side_effect=RuntimeError("fallo auditoria"),
        ):
            with self.assertRaises(RuntimeError):
                self.post_pago("40.00")

        self.assertEqual(Pago.objects.count(), 0)
        self.factura.refresh_from_db()
        self.assertEqual(self.factura.total_pagado, Decimal("0.00"))
        self.assertEqual(self.factura.saldo_pendiente, Decimal("100.00"))
        self.assertEqual(self.factura.estado, "PENDIENTE")

    def test_put_cobrar_factura_no_esta_permitido(self):
        response = self.client.put(
            reverse("pagos:cobrar", args=[self.factura.id]),
            data={"valor_pagado": "10.00"},
        )

        self.assertEqual(response.status_code, 405)


class AnularPagoTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin_pagos",
            password="clave-segura",
        )
        self.usuario.groups.add(grupo)
        self.client.force_login(self.usuario)

        sector = Sector.objects.create(nombre="Sector Anulacion")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta Anulacion")
        abonado = Abonado.objects.create(
            codigo="AB-PAGO",
            cedula_ruc="0303030303",
            nombres="Pago",
            apellidos="Prueba",
            direccion="Calle Pago",
            sector=sector,
            ruta=ruta,
        )
        medidor = Medidor.objects.create(
            abonado=abonado,
            numero="MED-PAGO",
            lectura_inicial=Decimal("0.00"),
        )
        periodo = PeriodoFacturacion.objects.create(
            nombre="Julio 2026",
            anio=2026,
            mes=7,
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 31),
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
            numero="FAC-ANULAR-PAGO",
            abonado=abonado,
            periodo=periodo,
            lectura=lectura,
            subtotal=Decimal("50.00"),
            total=Decimal("50.00"),
            saldo_pendiente=Decimal("50.00"),
            estado="PENDIENTE",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )
        self.pago = Pago.objects.create(
            factura=self.factura,
            metodo_pago="EFECTIVO",
            valor_pagado=Decimal("50.00"),
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def test_get_muestra_confirmacion_sin_anular(self):
        response = self.client.get(
            reverse("pagos:anular", args=[self.pago.id])
        )

        self.assertEqual(response.status_code, 200)
        self.pago.refresh_from_db()
        self.assertFalse(self.pago.anulado)

    def test_post_sin_motivo_no_anula(self):
        response = self.client.post(
            reverse("pagos:anular", args=[self.pago.id]),
            {"motivo": ""},
        )

        self.assertRedirects(
            response,
            reverse("pagos:anular", args=[self.pago.id]),
        )
        self.pago.refresh_from_db()
        self.assertFalse(self.pago.anulado)

    def test_post_con_motivo_anula_pago(self):
        response = self.client.post(
            reverse("pagos:anular", args=[self.pago.id]),
            {"motivo": "Pago duplicado"},
        )

        self.assertRedirects(response, reverse("reportes:facturas_pagadas"))
        self.pago.refresh_from_db()
        self.assertTrue(self.pago.anulado)
        self.assertEqual(self.pago.motivo_anulacion, "Pago duplicado")

    def test_error_en_auditoria_revierte_anulacion_pago(self):
        with patch(
            "pagos.views.registrar_auditoria",
            side_effect=RuntimeError("fallo auditoria"),
        ):
            with self.assertRaises(RuntimeError):
                self.client.post(
                    reverse("pagos:anular", args=[self.pago.id]),
                    {"motivo": "Pago duplicado"},
                )

        self.pago.refresh_from_db()
        self.factura.refresh_from_db()
        self.assertFalse(self.pago.anulado)
        self.assertEqual(self.pago.motivo_anulacion, "")
        self.assertEqual(self.factura.total_pagado, Decimal("50.00"))
        self.assertEqual(self.factura.saldo_pendiente, Decimal("0.00"))
        self.assertEqual(self.factura.estado, "PAGADA")

    def test_put_no_esta_permitido(self):
        response = self.client.put(
            reverse("pagos:anular", args=[self.pago.id]),
            data={"motivo": "No permitido"},
        )

        self.assertEqual(response.status_code, 405)
