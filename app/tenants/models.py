from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models

from .modules import modulos_por_defecto, normalizar_modulos


class Tenant(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    activo = models.BooleanField(default=True)
    slug = models.SlugField(
        max_length=50,
        unique=True,
        validators=[
            RegexValidator(
                regex=r"^[a-z0-9-]+$",
                message="Use solo minusculas, numeros y guiones.",
            )
        ],
    )
    nombre = models.CharField(max_length=150)
    db_name = models.CharField(max_length=100, unique=True, blank=True)
    modulos_habilitados = models.JSONField(default=modulos_por_defecto)

    class Meta:
        verbose_name = "Tenant"
        verbose_name_plural = "Tenants"
        ordering = ["nombre"]

    def save(self, *args, **kwargs):
        self.slug = self.slug.strip().lower()
        self.modulos_habilitados = normalizar_modulos(self.modulos_habilitados)

        if not self.db_name:
            self.db_name = self.construir_db_name(self.slug)

        super().save(*args, **kwargs)

    @staticmethod
    def construir_db_name(slug):
        return f"{settings.TENANT_DB_PREFIX}{slug}"

    @property
    def ruta_base(self):
        return f"/{self.slug}/"

    def __str__(self):
        return self.nombre
