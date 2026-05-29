from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError

from nucleo.models import ModeloBase
from abonados.models import Abonado


class SuspensionServicio(ModeloBase):
    ESTADOS = (
        ("SUSPENDIDO", "Suspendido"),
        ("RECONECTADO", "Reconectado"),
        ("ANULADO", "Anulado"),
    )

    abonado = models.ForeignKey(
        Abonado,
        on_delete=models.PROTECT,
        related_name="suspensiones"
    )

    fecha_suspension = models.DateField(default=timezone.localdate)
    motivo_suspension = models.TextField()

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="SUSPENDIDO"
    )

    fecha_reconexion = models.DateField(null=True, blank=True)
    observacion_reconexion = models.TextField(blank=True, default="")

    motivo_anulacion = models.TextField(blank=True, default="")
    fecha_anulacion = models.DateTimeField(null=True, blank=True)


    class Meta:
        verbose_name = "Suspensión de servicio"
        verbose_name_plural = "Suspensiones de servicio"
        ordering = ["-fecha_suspension"]

    def clean(self):
        if self.estado == "RECONECTADO" and not self.fecha_reconexion:
            raise ValidationError("Debe registrar la fecha de reconexión.")

    def __str__(self):
        return f"{self.abonado} - {self.estado}"