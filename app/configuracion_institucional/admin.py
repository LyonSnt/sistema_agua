from django.contrib import admin
from .models import ConfiguracionInstitucional


@admin.register(ConfiguracionInstitucional)
class ConfiguracionInstitucionalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "nombre_corto", "ruc", "telefono", "correo")
