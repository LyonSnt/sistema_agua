from django.conf import settings
from django.db import models


class Auditoria(models.Model):
    ACCIONES = (
        ("CREAR", "Crear"),
        ("ACTUALIZAR", "Actualizar"),
        ("ELIMINAR", "Eliminar"),
        ("PAGO", "Pago"),
        ("ANULAR_PAGO", "Anular pago"),
        ("ANULAR_FACTURA", "Anular factura"),
        ("GENERAR_FACTURA", "Generar factura"),
        ("LECTURA", "Lectura"),
        ("LOGIN", "Inicio de sesión"),
        ("LOGOUT", "Cierre de sesión"),
        ("IMPORTAR_LECTURAS", "Importar lecturas"),
        ("SUSPENDER_SERVICIO", "Suspender servicio"),
        ("RECONECTAR_SERVICIO", "Reconectar servicio"),
        ("CREAR_MULTA", "Crear multa"),
        ("COBRAR_MULTA", "Cobrar multa"),
        ("ANULAR_MULTA", "Anular multa"),
        ("AGREGAR_RUBRO", "Agregar rubro"),
        ("CREAR_MEDIDOR", "Crear medidor"),
        ("EDITAR_MEDIDOR", "Editar medidor"),
        ("CAMBIAR_MEDIDOR", "Cambiar medidor"),
        ("EXPORTAR_REPORTE", "Exportar reporte"),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    accion = models.CharField(max_length=50, choices=ACCIONES)
    modulo = models.CharField(max_length=100)
    descripcion = models.TextField()

    objeto_id = models.CharField(max_length=100, blank=True)
    objeto_repr = models.CharField(max_length=255, blank=True)

    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Auditoría"
        verbose_name_plural = "Auditoría"
        ordering = ["-creado_en"]

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.modulo}"
