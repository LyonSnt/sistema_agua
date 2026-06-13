from datetime import date
from decimal import Decimal
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import AnonymousUser, Group
from django.test import RequestFactory, TestCase

from abonados.models import Abonado, Ruta, Sector
from facturacion.models import Factura
from lecturas.models import Lectura, PeriodoFacturacion
from medidores.models import Medidor
from pagos.models import Pago
from usuarios.models import Usuario

from .context_processors import menu_sidebar
from .menu import MENU_SIDEBAR


class MenuSidebarTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.grupo_admin = Group.objects.create(name="Administrador")
        self.usuario = Usuario.objects.create_user(
            username="admin-menu",
            password="clave-segura",
            is_staff=True,
        )
        self.usuario.groups.add(self.grupo_admin)

    def test_menu_vacio_para_usuario_anonimo(self):
        request = self.factory.get("/login/")
        request.user = AnonymousUser()

        contexto = menu_sidebar(request)

        self.assertEqual(contexto["menu_sidebar"], [])

    def test_menu_prefija_urls_de_tenant_y_marca_activo(self):
        request = self.factory.get("/rumipamba/abonados/")
        request.user = self.usuario
        request.tenant_path_prefix = "/rumipamba"
        request.tenant = type("Tenant", (), {
            "modulos_habilitados": ["panel", "abonados", "admin"],
        })()

        contexto = menu_sidebar(request)
        items = [
            item
            for seccion in contexto["menu_sidebar"]
            for item in seccion["items"]
        ]

        abonados = next(item for item in items if item["texto"] == "Abonados")
        self.assertEqual(abonados["url"], "/rumipamba/abonados/")
        self.assertTrue(abonados["activo"])
        self.assertFalse(any(item["texto"] == "Medidores" for item in items))

    def test_menu_legacy_no_prefija_urls_sin_tenant(self):
        request = self.factory.get("/panel/")
        request.user = self.usuario
        request.tenant_path_prefix = ""
        request.tenant = None

        contexto = menu_sidebar(request)
        items = [
            item
            for seccion in contexto["menu_sidebar"]
            for item in seccion["items"]
        ]

        panel = next(item for item in items if item["texto"] == "Panel principal")
        self.assertEqual(panel["url"], "/panel/")
        self.assertTrue(panel["activo"])

    def test_todos_los_items_del_menu_tienen_icono(self):
        items_sin_icono = [
            item["texto"]
            for seccion in MENU_SIDEBAR
            for item in seccion["items"]
            if not item.get("icono")
        ]

        self.assertEqual(items_sin_icono, [])


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
