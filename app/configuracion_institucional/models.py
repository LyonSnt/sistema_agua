from django.db import models


class ConfiguracionInstitucional(models.Model):
    nombre = models.CharField(max_length=200)
    ruc = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    correo = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    class Meta:
        verbose_name = "Configuración institucional"
        verbose_name_plural = "Configuración institucional"

    def __str__(self):
        return self.nombre