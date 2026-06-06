from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from facturacion.models import Factura
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import CambioMedidor, Medidor
from multas.models import Multa
from usuarios.models import Usuario


class PanelAlertasTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin-panel",
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
            estado_servicio="SUSPENDIDO",
        )

        self.medidor_anterior = Medidor.objects.create(
            abonado=self.abonado,
            numero="MED001",
            lectura_inicial=Decimal("10.00"),
            estado="RETIRADO",
        )
        self.medidor_nuevo = Medidor.objects.create(
            abonado=self.abonado,
            numero="MED002",
            lectura_inicial=Decimal("0.00"),
            estado="ACTIVO",
        )
        CambioMedidor.objects.create(
            abonado=self.abonado,
            medidor_anterior=self.medidor_anterior,
            medidor_nuevo=self.medidor_nuevo,
            fecha_cambio=date.today(),
            lectura_final_anterior=Decimal("35.50"),
            lectura_inicial_nuevo=Decimal("0.00"),
            motivo="Medidor dañado",
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
            medidor=self.medidor_nuevo,
            lectura_anterior=Decimal("0.00"),
            lectura_actual=Decimal("0.00"),
            lectura_registrada=False,
        )
        Factura.objects.create(
            numero="FAC001",
            abonado=self.abonado,
            periodo=periodo,
            lectura=lectura,
            subtotal=Decimal("0.00"),
            total=Decimal("0.00"),
            total_pagado=Decimal("0.00"),
            saldo_pendiente=Decimal("0.00"),
            estado="PAGADA",
        )
        Multa.objects.create(
            abonado=self.abonado,
            tipo="OTRA",
            motivo="Prueba de multa",
            fecha=date.today(),
            valor=Decimal("12.00"),
            estado="PENDIENTE",
        )

    def test_panel_muestra_alertas_operativas(self):
        response = self.client.get(reverse("panel:inicio"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Atención requerida")
        self.assertContains(response, "Abonados suspendidos")
        self.assertContains(response, "Pendientes de reconexión")
        self.assertContains(response, "Multas pendientes")
        self.assertContains(response, "Cambios de medidor recientes")
        self.assertContains(response, "Agua Ana")
        self.assertContains(response, "Prueba de multa")
        self.assertContains(response, "MED001")
        self.assertContains(response, "MED002")
