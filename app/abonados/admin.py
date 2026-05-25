from django.contrib import admin

from .models import Sector, Ruta, Abonado


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activo", "creado_en", "actualizado_en")
    search_fields = ("nombre",)
    list_filter = ("activo",)


@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "sector", "activo", "creado_en")
    search_fields = ("nombre", "sector__nombre")
    list_filter = ("sector", "activo")


@admin.register(Abonado)
class AbonadoAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "cedula_ruc",
        "apellidos",
        "nombres",
        "telefono",
        "sector",
        "ruta",
        "activo",
    )

    search_fields = (
        "codigo",
        "cedula_ruc",
        "nombres",
        "apellidos",
        "telefono",
    )

    list_filter = (
        "sector",
        "ruta",
        "activo",
    )

    readonly_fields = (
        "creado_en",
        "actualizado_en",
        "creado_por",
        "actualizado_por",
    )

    fieldsets = (
        ("Datos principales", {
            "fields": (
                "codigo",
                "cedula_ruc",
                "nombres",
                "apellidos",
                "telefono",
                "correo",
            )
        }),
        ("Ubicación", {
            "fields": (
                "direccion",
                "referencia",
                "sector",
                "ruta",
            )
        }),
        ("Estado", {
            "fields": (
                "activo",
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