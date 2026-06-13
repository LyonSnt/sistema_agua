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
        self.supervisor = self.crear_usuario("Supervisor", "supervisor-abonado")
        self.consulta = self.crear_usuario("Consulta", "consulta-abonado")

        self.sector = Sector.objects.create(nombre="Sector A")
        self.ruta = Ruta.objects.create(sector=self.sector, nombre="Ruta A")
        self.otro_sector = Sector.objects.create(nombre="Sector B")
        self.otra_ruta = Ruta.objects.create(
            sector=self.otro_sector,
            nombre="Ruta B",
        )
        self.abonado = Abonado.objects.create(
            codigo="AB001",
            cedula_ruc="0101010101",
            nombres="Ana",
            apellidos="Agua",
            direccion="Calle 1",
            sector=self.sector,
            ruta=self.ruta,
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

    def test_descarga_pdf_registra_auditoria(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("abonados:detalle_pdf", args=[self.abonado.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(
            Auditoria.objects.filter(
                accion="EXPORTAR_REPORTE",
                modulo="Abonados",
                objeto_id=str(self.abonado.id),
            ).exists()
        )

    def datos_abonado(self, **overrides):
        datos = {
            "codigo": "AB002",
            "cedula_ruc": "0202020202",
            "nombres": "Bruno",
            "apellidos": "Barrera",
            "telefono": "0999999999",
            "correo": "bruno@example.com",
            "direccion": "Calle 2",
            "referencia": "Casa azul",
            "sector": self.sector.id,
            "ruta": self.ruta.id,
            "estado_servicio": "ACTIVO",
            "activo": "on",
        }
        datos.update(overrides)
        return datos

    def test_supervisor_puede_crear_abonado(self):
        self.client.force_login(self.supervisor)

        response = self.client.post(
            reverse("abonados:crear"),
            self.datos_abonado(),
        )

        abonado = Abonado.objects.get(codigo="AB002")
        self.assertRedirects(
            response,
            reverse("abonados:detalle", args=[abonado.id]),
        )
        self.assertEqual(abonado.creado_por, self.supervisor)
        self.assertEqual(abonado.actualizado_por, self.supervisor)
        self.assertTrue(
            Auditoria.objects.filter(
                accion="CREAR",
                modulo="Abonados",
                objeto_id=str(abonado.id),
            ).exists()
        )

    def test_consulta_no_puede_crear_abonado(self):
        self.client.force_login(self.consulta)

        response = self.client.get(reverse("abonados:crear"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))

    def test_admin_puede_editar_abonado(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("abonados:editar", args=[self.abonado.id]),
            self.datos_abonado(
                codigo=self.abonado.codigo,
                cedula_ruc=self.abonado.cedula_ruc,
                nombres="Ana Maria",
                apellidos=self.abonado.apellidos,
            ),
        )

        self.abonado.refresh_from_db()
        self.assertRedirects(
            response,
            reverse("abonados:detalle", args=[self.abonado.id]),
        )
        self.assertEqual(self.abonado.nombres, "Ana Maria")
        self.assertEqual(self.abonado.actualizado_por, self.admin)
        self.assertTrue(
            Auditoria.objects.filter(
                accion="ACTUALIZAR",
                modulo="Abonados",
                objeto_id=str(self.abonado.id),
            ).exists()
        )

    def test_no_permite_ruta_de_otro_sector(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("abonados:crear"),
            self.datos_abonado(
                sector=self.sector.id,
                ruta=self.otra_ruta.id,
            ),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "La ruta seleccionada no pertenece al sector indicado.",
        )
        self.assertFalse(Abonado.objects.filter(codigo="AB002").exists())

    def test_formulario_no_expone_estado_servicio_ni_activo(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse("abonados:crear"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'name="estado_servicio"')
        self.assertNotContains(response, 'name="activo"')

    def test_listado_filtra_abonados_por_estado(self):
        Abonado.objects.create(
            codigo="AB003",
            cedula_ruc="0303030303",
            nombres="Carla",
            apellidos="Cancelada",
            direccion="Calle 3",
            sector=self.sector,
            ruta=self.ruta,
            activo=False,
        )
        self.client.force_login(self.admin)

        response = self.client.get(reverse("abonados:lista"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "AB001")
        self.assertNotContains(response, "AB003")

        response = self.client.get(
            reverse("abonados:lista"),
            {"estado": "inactivos"},
        )

        self.assertContains(response, "AB003")
        self.assertNotContains(response, "AB001")

        response = self.client.get(
            reverse("abonados:lista"),
            {"estado": "todos"},
        )

        self.assertContains(response, "AB001")
        self.assertContains(response, "AB003")

    def test_admin_puede_desactivar_abonado(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("abonados:cambiar_estado", args=[self.abonado.id]),
            {"accion": "desactivar"},
        )

        self.abonado.refresh_from_db()
        self.assertRedirects(response, reverse("abonados:lista"))
        self.assertFalse(self.abonado.activo)
        self.assertEqual(self.abonado.actualizado_por, self.admin)
        self.assertTrue(
            Auditoria.objects.filter(
                accion="DESACTIVAR",
                modulo="Abonados",
                objeto_id=str(self.abonado.id),
            ).exists()
        )

    def test_supervisor_puede_reactivar_abonado(self):
        self.abonado.activo = False
        self.abonado.save(update_fields=["activo"])
        self.client.force_login(self.supervisor)

        response = self.client.post(
            reverse("abonados:cambiar_estado", args=[self.abonado.id]),
            {"accion": "reactivar"},
        )

        self.abonado.refresh_from_db()
        self.assertRedirects(response, reverse("abonados:lista"))
        self.assertTrue(self.abonado.activo)
        self.assertEqual(self.abonado.actualizado_por, self.supervisor)
        self.assertTrue(
            Auditoria.objects.filter(
                accion="REACTIVAR",
                modulo="Abonados",
                objeto_id=str(self.abonado.id),
            ).exists()
        )

    def test_consulta_no_puede_cambiar_estado_abonado(self):
        self.client.force_login(self.consulta)

        response = self.client.post(
            reverse("abonados:cambiar_estado", args=[self.abonado.id]),
            {"accion": "desactivar"},
        )

        self.abonado.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], reverse("panel:inicio"))
        self.assertTrue(self.abonado.activo)
        self.assertFalse(
            Auditoria.objects.filter(
                accion="DESACTIVAR",
                modulo="Abonados",
                objeto_id=str(self.abonado.id),
            ).exists()
        )
