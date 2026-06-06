from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from auditoria.models import Auditoria
from medidores.models import CambioMedidor, Medidor
from multas.models import Multa
from usuarios.models import Usuario

from .models import Abonado, Ruta, Sector


class DetalleAbonadoTests(TestCase):
    def crear_usuario(self, rol, username):
        grupo, _ = Group.objects.get_or_create(name=rol)
        usuario = Usuario.objects.create_user(
            username=username,
            password="clave-segura",
        )
        usuario.groups.add(grupo)
        return usuario

    def setUp(self):
        self.admin = self.crear_usuario("Administrador", "admin-abonado")
        self.consulta = self.crear_usuario("Consulta", "consulta-abonado")

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
            fecha_cambio=date(2026, 6, 6),
            lectura_final_anterior=Decimal("35.50"),
            lectura_inicial_nuevo=Decimal("0.00"),
            motivo="Medidor dañado",
        )

        Multa.objects.create(
            abonado=self.abonado,
            tipo="OTRA",
            motivo="Prueba de multa",
            fecha=date(2026, 6, 1),
            valor=Decimal("12.00"),
        )

        Auditoria.objects.create(
            usuario=self.admin,
            accion="CAMBIAR_MEDIDOR",
            modulo="Medidores",
            descripcion=f"Cambió medidor para {self.abonado}",
            objeto_repr=str(self.abonado),
        )

    def test_ficha_muestra_historial_integral(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("abonados:detalle", args=[self.abonado.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Medidores del abonado")
        self.assertContains(response, "MED001")
        self.assertContains(response, "MED002")
        self.assertContains(response, "Historial de cambios de medidor")
        self.assertContains(response, "Medidor dañado")
        self.assertContains(response, "Multas del abonado")
        self.assertContains(response, "Prueba de multa")
        self.assertContains(response, "Actividad relacionada")
        self.assertContains(response, "Cambió medidor para")

    def test_usuario_no_admin_no_ve_auditoria_relacionada(self):
        self.client.force_login(self.consulta)

        response = self.client.get(
            reverse("abonados:detalle", args=[self.abonado.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Medidores del abonado")
        self.assertNotContains(response, "Actividad relacionada")
        self.assertNotContains(response, "Cambió medidor para")
