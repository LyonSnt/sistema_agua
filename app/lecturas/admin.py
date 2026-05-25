from django.contrib import admin

from .models import PeriodoFacturacion, Lectura
from facturacion.servicios import generar_factura_desde_lectura


@admin.register(PeriodoFacturacion)
class PeriodoFacturacionAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "anio",
        "mes",
        "fecha_inicio",
        "fecha_fin",
        "estado",
        "activo",
    )

    search_fields = ("nombre",)

    list_filter = (
        "anio",
        "mes",
        "estado",
        "activo",
    )


@admin.register(Lectura)
class LecturaAdmin(admin.ModelAdmin):

    actions = ["generar_facturas"]

    @admin.action(description="Generar factura desde lecturas seleccionadas")
    def generar_facturas(self, request, queryset):
        generadas = 0
        existentes = 0
        errores = 0

        for lectura in queryset:
            try:
                ya_tenia = hasattr(lectura, "factura")
                generar_factura_desde_lectura(lectura, request.user)

                if ya_tenia:
                    existentes += 1
                else:
                    generadas += 1

            except Exception:
                errores += 1

        self.message_user(
            request,
            f"Facturas generadas: {generadas}. Ya existentes: {existentes}. Errores: {errores}."
        )
    list_display = (
        "periodo",
        "medidor",
        "lectura_anterior",
        "lectura_actual",
        "consumo",
        "activo",
    )

    search_fields = (
        "medidor__numero",
        "medidor__abonado__nombres",
        "medidor__abonado__apellidos",
        "medidor__abonado__cedula_ruc",
    )

    list_filter = (
        "periodo",
        "activo",
    )

    readonly_fields = (
        "consumo",
        "creado_en",
        "actualizado_en",
        "creado_por",
        "actualizado_por",
    )

    fieldsets = (
        ("Datos de lectura", {
            "fields": (
                "periodo",
                "medidor",
                "lectura_anterior",
                "lectura_actual",
                "consumo",
                "observacion",
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