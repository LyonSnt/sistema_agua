from django.contrib import admin

from .models import Factura, FacturaDetalle


class FacturaDetalleInline(admin.TabularInline):
    model = FacturaDetalle
    extra = 0
    readonly_fields = ("valor_total",)


@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "abonado",
        "periodo",
        "subtotal",
        "descuento",
        "total",
        "total_pagado",
        "saldo_pendiente",
        "estado",
        "fecha_emision",
    )

    search_fields = (
        "numero",
        "abonado__nombres",
        "abonado__apellidos",
        "abonado__cedula_ruc",
    )

    list_filter = (
        "estado",
        "periodo",
        "fecha_emision",
    )

    readonly_fields = (
        "subtotal",
        "total",
        "total_pagado",
        "saldo_pendiente",
        "fecha_emision",
        "creado_en",
        "actualizado_en",
        "creado_por",
        "actualizado_por",
    )

    inlines = [FacturaDetalleInline]

    fieldsets = (
        ("Datos principales", {
            "fields": (
                "numero",
                "abonado",
                "periodo",
                "lectura",
                "estado",
            )
        }),
        ("Valores", {
            "fields": (
                "subtotal",
                "descuento",
                "total",
            )
        }),
        ("Observación", {
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


@admin.register(FacturaDetalle)
class FacturaDetalleAdmin(admin.ModelAdmin):
    list_display = (
        "factura",
        "descripcion",
        "cantidad",
        "valor_unitario",
        "valor_total",
        "tipo",
    )

    search_fields = (
        "factura__numero",
        "descripcion",
    )

    list_filter = (
        "tipo",
    )