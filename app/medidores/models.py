from django.db import models

from nucleo.models import ModeloBase
from abonados.models import Abonado


class Medidor(ModeloBase):
    ESTADOS = (
        ("ACTIVO", "Activo"),
        ("DANADO", "Dañado"),
        ("SUSPENDIDO", "Suspendido"),
        ("RETIRADO", "Retirado"),
    )

    abonado = models.ForeignKey(
        Abonado,
        on_delete=models.PROTECT,
        related_name="medidores"
    )

    numero = models.CharField(
        max_length=50,
        unique=True
    )

    marca = models.CharField(
        max_length=100,
        blank=True
    )

    modelo = models.CharField(
        max_length=100,
        blank=True
    )

    lectura_inicial = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    fecha_instalacion = models.DateField(
        null=True,
        blank=True
    )

    estado = models.CharField(
        max_length=20,
        choices=ESTADOS,
        default="ACTIVO"
    )

    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Medidor"
        verbose_name_plural = "Medidores"
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero} - {self.abonado}"


class CambioMedidor(ModeloBase):
    abonado = models.ForeignKey(Abonado, on_delete=models.PROTECT)
    medidor_anterior = models.ForeignKey(
        Medidor,
        on_delete=models.PROTECT,
        related_name="cambios_como_anterior"
    )
    medidor_nuevo = models.ForeignKey(
        Medidor,
        on_delete=models.PROTECT,
        related_name="cambios_como_nuevo"
    )
    fecha_cambio = models.DateField()
    lectura_final_anterior = models.DecimalField(max_digits=10, decimal_places=2)
    lectura_inicial_nuevo = models.DecimalField(max_digits=10, decimal_places=2)
    motivo = models.TextField()