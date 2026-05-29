from django.db import models

from nucleo.models import ModeloBase


class Sector(ModeloBase):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Sector"
        verbose_name_plural = "Sectores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Ruta(ModeloBase):
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="rutas"
    )

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Ruta"
        verbose_name_plural = "Rutas"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.sector} - {self.nombre}"


class Abonado(ModeloBase):
    codigo = models.CharField(max_length=20, unique=True)
    cedula_ruc = models.CharField(
        max_length=20,
        unique=True
    )
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    telefono = models.CharField(
        max_length=20,
        blank=True
    )
    correo = models.EmailField(blank=True)
    direccion = models.TextField()
    referencia = models.TextField(blank=True)
    sector = models.ForeignKey(
        Sector,
        on_delete=models.PROTECT,
        related_name="abonados"
    )
    ruta = models.ForeignKey(
        Ruta,
        on_delete=models.PROTECT,
        related_name="abonados"
    )
    ESTADOS_SERVICIO = (
        ("ACTIVO", "Activo"),
        ("SUSPENDIDO", "Suspendido"),
    )

    estado_servicio = models.CharField(
        max_length=20,
        choices=ESTADOS_SERVICIO,
        default="ACTIVO"
    )


    class Meta:
        verbose_name = "Abonado"
        verbose_name_plural = "Abonados"
        ordering = ["apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos} {self.nombres}"
    
    def estado_cuenta(self):
        facturas_pendientes = self.facturas.filter(
            activo=True,
            estado__in=["PENDIENTE", "PARCIAL"]
        ).count()

        if facturas_pendientes == 0:
            return "AL_DIA"

        if facturas_pendientes == 1:
            return "CON_DEUDA"

        return "MOROSO"