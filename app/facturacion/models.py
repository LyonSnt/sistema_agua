from decimal import Decimal

from django.db import models

from nucleo.models import ModeloBase
from abonados.models import Abonado
from lecturas.models import Lectura, PeriodoFacturacion


class Factura(ModeloBase):
    ESTADOS = (
        ("PENDIENTE", "Pendiente"),
        ("PARCIAL", "Pago parcial"),
        ("PAGADA", "Pagada"),
        ("ANULADA", "Anulada"),
    )

    numero = models.CharField(max_length=30, unique=True)

    abonado = models.ForeignKey(
        Abonado,
        on_delete=models.PROTECT,
        related_name="facturas"
    )

    periodo = models.ForeignKey(
        PeriodoFacturacion,
        on_delete=models.PROTECT,
        related_name="facturas"
    )

    lectura = models.OneToOneField(
        Lectura,
        on_delete=models.PROTECT,
        related_name="factura"
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    saldo_pendiente = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="PENDIENTE"
    )

    fecha_anulacion = models.DateTimeField(null=True, blank=True)
    motivo_anulacion = models.TextField(blank=True, default="")

    fecha_emision = models.DateField(auto_now_add=True)
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"
        ordering = ["-fecha_emision", "-numero"]
        unique_together = ("abonado", "periodo")

    def calcular_totales(self):
        subtotal = sum(
            detalle.valor_total for detalle in self.detalles.all()
        )
        self.subtotal = subtotal
        self.total = subtotal - self.descuento
        self.saldo_pendiente = self.total - self.total_pagado
        self.save(update_fields=["subtotal", "total", "saldo_pendiente"])

    def __str__(self):
        return f"{self.numero} - {self.abonado} - Total: ${self.total}"
    
    def actualizar_estado_pago(self):
        total_pagado = sum(
            pago.valor_pagado
            for pago in self.pagos.filter(
                activo=True,
                anulado=False
            )
        )
        self.total_pagado = total_pagado
        self.saldo_pendiente = self.total - total_pagado

        if self.total_pagado <= 0:
            self.estado = "PENDIENTE"
        elif self.total_pagado < self.total:
            self.estado = "PARCIAL"
        else:
            self.estado = "PAGADA"
            self.saldo_pendiente = 0

        self.save(update_fields=["total_pagado", "saldo_pendiente", "estado"])


class FacturaDetalle(ModeloBase):
    factura = models.ForeignKey(
        Factura,
        on_delete=models.CASCADE,
        related_name="detalles"
    )

    descripcion = models.CharField(max_length=200)
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    tipo = models.CharField(
        max_length=50,
        blank=True,
        help_text="Ejemplo: AGUA, ALCANTARILLADO, MULTA, OTRO"
    )

    class Meta:
        verbose_name = "Detalle de factura"
        verbose_name_plural = "Detalles de factura"

    def save(self, *args, **kwargs):
        self.valor_total = Decimal(self.cantidad) * Decimal(self.valor_unitario)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.descripcion} - {self.factura.numero}"