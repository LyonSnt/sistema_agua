from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from abonados.models import Abonado, Ruta, Sector
from facturacion.models import Factura
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import Medidor
from pagos.models import Pago


class VerificarConsistenciaCommandTests(TestCase):
    def setUp(self):
        self.sector = Sector.objects.create(nombre="Sector Consistencia")
        self.ruta = Ruta.objects.create(
            sector=self.sector,
            nombre="Ruta Consistencia",
        )
        self.abonado = Abonado.objects.create(
            codigo="AB-CONS",
            cedula_ruc="0707070707",
            nombres="Consistencia",
            apellidos="Operativa",
            direccion="Calle Consistencia",
            sector=self.sector,
            ruta=self.ruta,
        )
        self.medidor = Medidor.objects.create(
            abonado=self.abonado,
            numero="MED-CONS",
            lectura_inicial=Decimal("0.00"),
        )
        self.periodo = PeriodoFacturacion.objects.create(
            nombre="Septiembre 2026",
            anio=2026,
            mes=9,
            fecha_inicio=date(2026, 9, 1),
            fecha_fin=date(2026, 9, 30),
            estado="ABIERTO",
        )

    def crear_lectura(self, actual="10.00"):
        return Lectura.objects.create(
            periodo=self.periodo,
            medidor=self.medidor,
            lectura_anterior=Decimal("0.00"),
            lectura_actual=Decimal(actual),
            lectura_registrada=True,
        )

    def crear_factura(self, numero="FAC-CONS-001", total="100.00"):
        lectura = self.crear_lectura()
        return Factura.objects.create(
            numero=numero,
            abonado=self.abonado,
            periodo=self.periodo,
            lectura=lectura,
            subtotal=Decimal(total),
            total=Decimal(total),
            saldo_pendiente=Decimal(total),
            estado="PENDIENTE",
        )

    def ejecutar_comando(self, *args):
        salida = StringIO()
        call_command("verificar_consistencia", *args, stdout=salida)
        return salida.getvalue()

    def test_sin_inconsistencias_muestra_ok(self):
        factura = self.crear_factura()
        Pago.objects.create(
            factura=factura,
            metodo_pago="EFECTIVO",
            valor_pagado=Decimal("100.00"),
        )

        salida = self.ejecutar_comando()

        self.assertIn("default: sin inconsistencias", salida)
        self.assertIn("No se encontraron inconsistencias operativas", salida)

    def test_detecta_factura_con_saldo_descuadrado(self):
        factura = self.crear_factura(numero="FAC-DESC")
        Pago.objects.create(
            factura=factura,
            metodo_pago="EFECTIVO",
            valor_pagado=Decimal("40.00"),
        )
        Factura.objects.filter(id=factura.id).update(
            total_pagado=Decimal("0.00"),
            saldo_pendiente=Decimal("100.00"),
            estado="PENDIENTE",
        )

        salida = self.ejecutar_comando()

        self.assertIn("Facturas con saldo o total pagado descuadrado", salida)
        self.assertIn("FAC-DESC", salida)
        self.assertIn("Inconsistencias encontradas", salida)

    def test_detecta_lectura_registrada_sin_factura(self):
        lectura = self.crear_lectura()

        salida = self.ejecutar_comando()

        self.assertIn("Lecturas registradas sin factura", salida)
        self.assertIn(f"lectura={lectura.id}", salida)

    def test_fail_on_issues_lanza_error(self):
        self.crear_lectura()

        with self.assertRaises(CommandError):
            self.ejecutar_comando("--fail-on-issues")
