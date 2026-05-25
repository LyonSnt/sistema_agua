from django.db import models

from nucleo.models import ModeloBase


class TarifaAgua(ModeloBase):
    nombre = models.CharField(max_length=100, unique=True)

    valor_base = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    consumo_base = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Consumo incluido dentro del valor base."
    )

    valor_excedente = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Valor a cobrar por cada unidad adicional de consumo."
    )

    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Tarifa de agua"
        verbose_name_plural = "Tarifas de agua"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class RangoTarifaAgua(ModeloBase):
    tarifa = models.ForeignKey(
        TarifaAgua,
        on_delete=models.CASCADE,
        related_name="rangos"
    )

    desde = models.DecimalField(max_digits=10, decimal_places=2)

    hasta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Dejar vacío si no tiene límite superior."
    )

    valor_por_unidad = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    class Meta:
        verbose_name = "Rango de tarifa de agua"
        verbose_name_plural = "Rangos de tarifa de agua"
        ordering = ["desde"]

    def __str__(self):
        return f"{self.tarifa} | {self.desde} - {self.hasta or 'en adelante'}"


class Rubro(ModeloBase):
    TIPOS = (
        ("ALCANTARILLADO", "Alcantarillado"),
        ("MULTA", "Multa"),
        ("OTRO", "Otro"),
    )

    FORMAS_CALCULO = (
        ("FIJO", "Valor fijo"),
        ("PORCENTAJE", "Porcentaje"),
    )

    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=30, choices=TIPOS)

    forma_calculo = models.CharField(
        max_length=20,
        choices=FORMAS_CALCULO,
        default="FIJO"
    )

    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    aplica_automaticamente = models.BooleanField(default=False)
    vigente = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Rubro"
        verbose_name_plural = "Rubros"
        ordering = ["tipo", "nombre"]

    def __str__(self):
        return f"{self.nombre} - {self.tipo}"