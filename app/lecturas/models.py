from django.core.exceptions import ValidationError
from django.db import models

from nucleo.models import ModeloBase
from medidores.models import Medidor


class PeriodoFacturacion(ModeloBase):
    ESTADOS = (
        ("ABIERTO", "Abierto"),
        ("CERRADO", "Cerrado"),
    )

    nombre = models.CharField(max_length=100, unique=True)
    anio = models.PositiveIntegerField()
    mes = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="ABIERTO"
    )

    class Meta:
        verbose_name = "Período de facturación"
        verbose_name_plural = "Períodos de facturación"
        ordering = ["-anio", "-mes"]
        unique_together = ("anio", "mes")

    def __str__(self):
        return self.nombre


class Lectura(ModeloBase):
    periodo = models.ForeignKey(
        PeriodoFacturacion,
        on_delete=models.PROTECT,
        related_name="lecturas"
    )

    medidor = models.ForeignKey(
        Medidor,
        on_delete=models.PROTECT,
        related_name="lecturas"
    )

    lectura_anterior = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    lectura_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    consumo = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        editable=False
    )

    observacion = models.TextField(blank=True)

    lectura_registrada = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Lectura"
        verbose_name_plural = "Lecturas"
        ordering = ["periodo", "medidor"]
        unique_together = ("periodo", "medidor")

    def clean(self):
        if self.lectura_actual < self.lectura_anterior:
            raise ValidationError(
                "La lectura actual no puede ser menor que la lectura anterior."
            )

    def save(self, *args, **kwargs):
        self.consumo = self.lectura_actual - self.lectura_anterior
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.medidor} - {self.periodo}"