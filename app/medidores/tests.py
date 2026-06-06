from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from usuarios.models import Usuario

from .models import CambioMedidor, Medidor


class CambioMedidorTests(TestCase):
    def setUp(self):
        grupo = Group.objects.create(name="Supervisor")
        self.usuario = Usuario.objects.create_user(
            username="supervisor",
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
        self.medidor = Medidor.objects.create(
            abonado=self.abonado,
            numero="MED001",
            lectura_inicial=Decimal("10.00"),
            estado="ACTIVO",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

    def datos_cambio(self, **overrides):
        datos = {
            "fecha_cambio": date(2026, 6, 6).isoformat(),
            "lectura_final_anterior": "35.50",
            "numero_nuevo": "MED002",
            "marca_nuevo": "Nueva marca",
            "modelo_nuevo": "Modelo X",
            "lectura_inicial_nuevo": "0.00",
            "motivo": "Medidor dañado",
        }
        datos.update(overrides)
        return datos

    def test_cambio_valido_crea_medidor_y_retira_anterior(self):
        response = self.client.post(
            reverse("medidores:cambiar", args=[self.medidor.id]),
            self.datos_cambio(),
        )

        medidor_nuevo = Medidor.objects.get(numero="MED002")
        self.assertRedirects(
            response,
            reverse("medidores:detalle", args=[medidor_nuevo.id]),
        )

        self.medidor.refresh_from_db()
        self.assertEqual(self.medidor.estado, "RETIRADO")
        self.assertEqual(self.medidor.actualizado_por, self.usuario)

        self.assertEqual(medidor_nuevo.abonado, self.abonado)
        self.assertEqual(medidor_nuevo.lectura_inicial, Decimal("0.00"))
        self.assertEqual(medidor_nuevo.estado, "ACTIVO")
        self.assertEqual(medidor_nuevo.creado_por, self.usuario)

        cambio = CambioMedidor.objects.get()
        self.assertEqual(cambio.abonado, self.abonado)
        self.assertEqual(cambio.medidor_anterior, self.medidor)
        self.assertEqual(cambio.medidor_nuevo, medidor_nuevo)
        self.assertEqual(cambio.lectura_final_anterior, Decimal("35.50"))
        self.assertEqual(cambio.motivo, "Medidor dañado")

    def test_rechaza_numero_duplicado_sin_crear_cambio(self):
        Medidor.objects.create(
            abonado=self.abonado,
            numero="MED002",
            lectura_inicial=Decimal("0.00"),
        )

        response = self.client.post(
            reverse("medidores:cambiar", args=[self.medidor.id]),
            self.datos_cambio(numero_nuevo="MED002"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un medidor con este número.")
        self.assertEqual(CambioMedidor.objects.count(), 0)

        self.medidor.refresh_from_db()
        self.assertEqual(self.medidor.estado, "ACTIVO")

    def test_no_permite_cambiar_medidor_retirado(self):
        self.medidor.estado = "RETIRADO"
        self.medidor.save(update_fields=["estado"])

        response = self.client.get(
            reverse("medidores:cambiar", args=[self.medidor.id])
        )

        self.assertRedirects(
            response,
            reverse("medidores:detalle", args=[self.medidor.id]),
        )
        self.assertEqual(CambioMedidor.objects.count(), 0)

    def test_cajero_no_puede_cambiar_medidor(self):
        grupo = Group.objects.create(name="Cajero")
        cajero = Usuario.objects.create_user(
            username="cajero",
            password="clave-segura",
        )
        cajero.groups.add(grupo)
        self.client.force_login(cajero)

        response = self.client.post(
            reverse("medidores:cambiar", args=[self.medidor.id]),
            self.datos_cambio(),
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))
        self.assertEqual(CambioMedidor.objects.count(), 0)
