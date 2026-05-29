from django.contrib import admin
from .models import SuspensionServicio


@admin.register(SuspensionServicio)
class SuspensionServicioAdmin(admin.ModelAdmin):
    list_display = (
        "abonado",
        "fecha_suspension",
        "estado",
        "fecha_reconexion",
        "activo",
    )

    search_fields = (
        "abonado__nombres",
        "abonado__apellidos",
        "abonado__cedula_ruc",
        "motivo_suspension",
    )

    list_filter = (
        "estado",
        "fecha_suspension",
        "activo",
    )