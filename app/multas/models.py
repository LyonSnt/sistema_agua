from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError

from nucleo.models import ModeloBase
from abonados.models import Abonado


class Multa(ModeloBase):
    ESTADOS = (
        ("PENDIENTE", "Pendiente"),
        ("PAGADA", "Pagada"),
        ("ANULADA", "Anulada"),
    )

    TIPOS = (
        ("INASISTENCIA_REUNION", "Inasistencia a reunión"),
        ("OTRA", "Otra"),
    )

    abonado = models.ForeignKey(
        Abonado,
        on_delete=models.PROTECT,
        related_name="multas"
    )

    tipo = models.CharField(max_length=50, choices=TIPOS)
    motivo = models.TextField()
    fecha = models.DateField()
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    fecha_pago = models.DateTimeField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=30, blank=True, default="")
    referencia = models.CharField(max_length=200, blank=True, default="")

    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = "Multa"
        verbose_name_plural = "Multas"
        ordering = ["-fecha", "abonado"]

    def clean(self):
        if self.valor <= Decimal("0.00"):
            raise ValidationError("El valor de la multa debe ser mayor a cero.")

    def __str__(self):
        return f"{self.abonado} - {self.get_tipo_display()} - ${self.valor}"