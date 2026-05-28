from django.contrib import admin
from .models import Multa


@admin.register(Multa)
class MultaAdmin(admin.ModelAdmin):
    list_display = (
        "abonado",
        "tipo",
        "fecha",
        "valor",
        "estado",
        "activo",
    )

    search_fields = (
        "abonado__nombres",
        "abonado__apellidos",
        "abonado__cedula_ruc",
        "motivo",
    )

    list_filter = (
        "tipo",
        "estado",
        "fecha",
        "activo",
    )

    readonly_fields = (
        "fecha_pago",
        "fecha_anulacion",
    )