from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from facturacion.models import Factura
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import Medidor
from multas.models import Multa
from pagos.models import Pago
from servicios.models import SuspensionServicio

from .models import Usuario


class MatrizPermisosRutasCriticasTests(TestCase):
    roles = [
        "Administrador",
        "Supervisor",
        "Cajero",
        "Lecturista",
        "Consulta",
    ]

    def setUp(self):
        self.usuarios = {}

        for rol in self.roles:
            grupo = Group.objects.create(name=rol)
            usuario = Usuario.objects.create_user(
                username=rol.lower(),
                password="clave-segura",
            )
            usuario.groups.add(grupo)
            self.usuarios[rol] = usuario

        sector = Sector.objects.create(nombre="Sector Permisos")
        ruta = Ruta.objects.create(sector=sector, nombre="Ruta Permisos")
        self.abonado = Abonado.objects.create(
            codigo="AB-PERM",
            cedula_ruc="0999999999",
            nombres="Permisos",
            apellidos="Prueba",
            direccion="Calle Permisos",
            sector=sector,
            ruta=ruta,
        )

        self.medidor = Medidor.objects.create(
            abonado=self.abonado,
            numero="MED-PERM",
            lectura_inicial=Decimal("0.00"),
            estado="ACTIVO",
        )

        self.periodo_pago = PeriodoFacturacion.objects.create(
            nombre="Junio Permisos",
            anio=2026,
            mes=6,
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 6, 30),
            estado="ABIERTO",
        )
        lectura_pago = Lectura.objects.create(
            periodo=self.periodo_pago,
            medidor=self.medidor,
            lectura_anterior=Decimal("0.00"),
            lectura_actual=Decimal("10.00"),
            lectura_registrada=True,
        )
        self.factura_pago = Factura.objects.create(
            numero="FAC-PAGO-PERM",
            abonado=self.abonado,
            periodo=self.periodo_pago,
            lectura=lectura_pago,
            subtotal=Decimal("100.00"),
            total=Decimal("100.00"),
            saldo_pendiente=Decimal("100.00"),
            estado="PENDIENTE",
        )
        self.pago = Pago.objects.create(
            factura=self.factura_pago,
            valor_pagado=Decimal("10.00"),
            metodo_pago="EFECTIVO",
        )

        self.periodo_anular = PeriodoFacturacion.objects.create(
            nombre="Julio Permisos",
            anio=2026,
            mes=7,
            fecha_inicio=date(2026, 7, 1),
            fecha_fin=date(2026, 7, 31),
            estado="ABIERTO",
        )
        lectura_anular = Lectura.objects.create(
            periodo=self.periodo_anular,
            medidor=self.medidor,
            lectura_anterior=Decimal("10.00"),
            lectura_actual=Decimal("20.00"),
            lectura_registrada=True,
        )
        self.factura_anular = Factura.objects.create(
            numero="FAC-ANULAR-PERM",
            abonado=self.abonado,
            periodo=self.periodo_anular,
            lectura=lectura_anular,
            subtotal=Decimal("20.00"),
            total=Decimal("20.00"),
            saldo_pendiente=Decimal("20.00"),
            estado="PENDIENTE",
        )

        self.multa = Multa.objects.create(
            abonado=self.abonado,
            tipo="OTRA",
            motivo="Multa permisos",
            fecha=date(2026, 6, 1),
            valor=Decimal("5.00"),
        )

        self.suspension = SuspensionServicio.objects.create(
            abonado=self.abonado,
            fecha_suspension=date(2026, 6, 1),
            motivo_suspension="Prueba permisos",
            estado="SUSPENDIDO",
        )

    def assert_redirige_panel(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))

    def assert_acceso_por_roles(self, nombre, url, permitidos):
        for rol in self.roles:
            with self.subTest(nombre=nombre, rol=rol):
                self.client.force_login(self.usuarios[rol])
                response = self.client.get(url)

                if rol in permitidos:
                    self.assertNotEqual(response.status_code, 302)
                else:
                    self.assert_redirige_panel(response)

    def test_matriz_permisos_rutas_criticas(self):
        casos = [
            (
                "anular factura",
                reverse("facturacion:anular", args=[self.factura_anular.id]),
                {"Administrador"},
            ),
            (
                "anular pago",
                reverse("pagos:anular", args=[self.pago.id]),
                {"Administrador"},
            ),
            (
                "anular multa",
                reverse("multas:anular", args=[self.multa.id]),
                {"Administrador"},
            ),
            (
                "cambiar medidor",
                reverse("medidores:cambiar", args=[self.medidor.id]),
                {"Administrador", "Supervisor"},
            ),
            (
                "suspender servicio",
                reverse("servicios:suspender"),
                {"Administrador", "Supervisor"},
            ),
            (
                "reconectar servicio",
                reverse("servicios:reconectar", args=[self.suspension.id]),
                {"Administrador", "Supervisor"},
            ),
            (
                "auditoria",
                reverse("auditoria:lista"),
                {"Administrador"},
            ),
            (
                "exportar auditoria",
                reverse("auditoria:exportar_excel"),
                {"Administrador"},
            ),
            (
                "exportar recaudacion diaria",
                reverse("reportes:recaudacion_diaria_excel"),
                {"Administrador", "Supervisor"},
            ),
            (
                "exportar cartera vencida",
                reverse("reportes:cartera_vencida_excel"),
                {"Administrador", "Supervisor"},
            ),
            (
                "cobrar factura",
                reverse("pagos:cobrar", args=[self.factura_pago.id]),
                {"Administrador", "Supervisor", "Cajero"},
            ),
            (
                "generar facturacion",
                reverse("facturacion:generar"),
                {"Administrador", "Supervisor"},
            ),
            (
                "registro masivo lecturas",
                reverse("lecturas:registro_masivo"),
                {"Administrador", "Supervisor", "Lecturista"},
            ),
        ]

        for nombre, url, permitidos in casos:
            self.assert_acceso_por_roles(nombre, url, permitidos)
