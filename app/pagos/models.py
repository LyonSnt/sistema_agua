from django.core.exceptions import ValidationError
from django.db import models

from nucleo.models import ModeloBase
from facturacion.models import Factura


class Pago(ModeloBase):
    METODOS_PAGO = (
        ("EFECTIVO", "Efectivo"),
        ("TRANSFERENCIA", "Transferencia"),
        ("OTRO", "Otro"),
    )

    factura = models.ForeignKey(
        Factura,
        on_delete=models.PROTECT,
        related_name="pagos"
    )

    fecha_pago = models.DateTimeField(auto_now_add=True)

    metodo_pago = models.CharField(
        max_length=30,
        choices=METODOS_PAGO,
        default="EFECTIVO"
    )

    valor_pagado = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    anulado = models.BooleanField(default=False)

    fecha_anulacion = models.DateTimeField(
        null=True,
        blank=True
    )

    motivo_anulacion = models.TextField(
        blank=True,
        default=""
    )

    referencia = models.CharField(max_length=200, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"
        ordering = ["-fecha_pago"]

    def clean(self):
        if self.anulado:
            return

        if self.factura.estado == "ANULADA":
            raise ValidationError("No se puede registrar pago de una factura anulada.")

        if self.valor_pagado <= 0:
            raise ValidationError("El valor pagado debe ser mayor a cero.")

        saldo = self.factura.saldo_pendiente or self.factura.total

        if self.valor_pagado > saldo:
            raise ValidationError(
                f"El valor pagado no puede ser mayor al saldo pendiente: ${saldo}."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        self.factura.actualizar_estado_pago()

    def __str__(self):
        return f"{self.factura.numero} - {self.valor_pagado}"