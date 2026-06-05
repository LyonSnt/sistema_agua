from datetime import date

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from abonados.models import Abonado, Ruta, Sector
from usuarios.models import Usuario

from .models import SuspensionServicio


class ServiciosTests(TestCase):
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

    def datos_suspension(self, **overrides):
        datos = {
            "abonado": self.abonado.id,
            "fecha_suspension": date(2026, 6, 1).isoformat(),
            "motivo_suspension": "Falta de pago",
        }
        datos.update(overrides)
        return datos

    def test_suspension_sin_motivo_no_crea_registro(self):
        response = self.client.post(
            reverse("servicios:suspender"),
            self.datos_suspension(motivo_suspension=""),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise los datos ingresados.")
        self.assertEqual(SuspensionServicio.objects.count(), 0)

    def test_suspension_con_abonado_invalido_no_crea_registro(self):
        response = self.client.post(
            reverse("servicios:suspender"),
            self.datos_suspension(abonado=9999),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise los datos ingresados.")
        self.assertEqual(SuspensionServicio.objects.count(), 0)

    def test_suspension_valida_crea_registro_y_suspende_abonado(self):
        response = self.client.post(
            reverse("servicios:suspender"),
            self.datos_suspension(),
        )

        self.assertRedirects(response, reverse("servicios:lista"))

        suspension = SuspensionServicio.objects.get()
        self.assertEqual(suspension.abonado, self.abonado)
        self.assertEqual(suspension.estado, "SUSPENDIDO")
        self.assertEqual(suspension.creado_por, self.usuario)
        self.assertEqual(suspension.actualizado_por, self.usuario)

        self.abonado.refresh_from_db()
        self.assertEqual(self.abonado.estado_servicio, "SUSPENDIDO")

    def test_put_suspender_servicio_no_esta_permitido(self):
        response = self.client.put(
            reverse("servicios:suspender"),
            data=self.datos_suspension(),
        )

        self.assertEqual(response.status_code, 405)

    def test_reconexion_sin_fecha_no_reconecta(self):
        suspension = SuspensionServicio.objects.create(
            abonado=self.abonado,
            fecha_suspension=date(2026, 6, 1),
            motivo_suspension="Falta de pago",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

        response = self.client.post(
            reverse("servicios:reconectar", args=[suspension.id]),
            {
                "fecha_reconexion": "",
                "observacion_reconexion": "Sin fecha",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Revise los datos ingresados.")

        suspension.refresh_from_db()
        self.assertEqual(suspension.estado, "SUSPENDIDO")
        self.assertIsNone(suspension.fecha_reconexion)

    def test_reconexion_valida_actualiza_suspension_y_abonado(self):
        self.abonado.estado_servicio = "SUSPENDIDO"
        self.abonado.save(update_fields=["estado_servicio"])
        suspension = SuspensionServicio.objects.create(
            abonado=self.abonado,
            fecha_suspension=date(2026, 6, 1),
            motivo_suspension="Falta de pago",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

        response = self.client.post(
            reverse("servicios:reconectar", args=[suspension.id]),
            {
                "fecha_reconexion": date(2026, 6, 5).isoformat(),
                "observacion_reconexion": "Pago regularizado",
            },
        )

        self.assertRedirects(response, reverse("servicios:lista"))

        suspension.refresh_from_db()
        self.assertEqual(suspension.estado, "RECONECTADO")
        self.assertEqual(suspension.fecha_reconexion, date(2026, 6, 5))
        self.assertEqual(suspension.actualizado_por, self.usuario)

        self.abonado.refresh_from_db()
        self.assertEqual(self.abonado.estado_servicio, "ACTIVO")

    def test_put_reconectar_servicio_no_esta_permitido(self):
        suspension = SuspensionServicio.objects.create(
            abonado=self.abonado,
            fecha_suspension=date(2026, 6, 1),
            motivo_suspension="Falta de pago",
            creado_por=self.usuario,
            actualizado_por=self.usuario,
        )

        response = self.client.put(
            reverse("servicios:reconectar", args=[suspension.id]),
            data={"fecha_reconexion": date(2026, 6, 5).isoformat()},
        )

        self.assertEqual(response.status_code, 405)
