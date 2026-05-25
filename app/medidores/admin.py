from django.contrib import admin

from .models import Medidor


@admin.register(Medidor)
class MedidorAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "abonado",
        "estado",
        "lectura_inicial",
        "fecha_instalacion",
        "activo",
    )

    search_fields = (
        "numero",
        "abonado__nombres",
        "abonado__apellidos",
        "abonado__cedula_ruc",
    )

    list_filter = (
        "estado",
        "activo",
    )

    readonly_fields = (
        "creado_en",
        "actualizado_en",
        "creado_por",
        "actualizado_por",
    )

    fieldsets = (
        ("Información principal", {
            "fields": (
                "abonado",
                "numero",
                "marca",
                "modelo",
            )
        }),

        ("Configuración", {
            "fields": (
                "lectura_inicial",
                "fecha_instalacion",
                "estado",
            )
        }),

        ("Observaciones", {
            "fields": (
                "observacion",
            )
        }),

        ("Auditoría", {
            "fields": (
                "creado_en",
                "actualizado_en",
                "creado_por",
                "actualizado_por",
            )
        }),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.creado_por = request.user

        obj.actualizado_por = request.user

        super().save_model(request, obj, form, change)