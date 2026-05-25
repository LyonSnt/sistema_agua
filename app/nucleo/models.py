from django.conf import settings
from django.db import models


class ModeloTiempo(models.Model):
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class ModeloEstado(models.Model):
    activo = models.BooleanField(default=True)

    class Meta:
        abstract = True


class ModeloAuditoria(models.Model):
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_creados",
    )
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_actualizados",
    )

    class Meta:
        abstract = True


class ModeloBase(ModeloTiempo, ModeloEstado, ModeloAuditoria):
    class Meta:
        abstract = True