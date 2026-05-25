from django.contrib import admin

from .models import Pago


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = (
        "factura",
        "fecha_pago",
        "metodo_pago",
        "valor_pagado",
        "activo",
    )

    search_fields = (
        "factura__numero",
        "factura__abonado__nombres",
        "factura__abonado__apellidos",
    )

    list_filter = (
        "metodo_pago",
        "fecha_pago",
        "activo",
    )

    readonly_fields = (
        "fecha_pago",
        "creado_en",
        "actualizado_en",
        "creado_por",
        "actualizado_por",
    )

    fieldsets = (
        ("Información del pago", {
            "fields": (
                "factura",
                "fecha_pago",
                "metodo_pago",
                "valor_pagado",
                "referencia",
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