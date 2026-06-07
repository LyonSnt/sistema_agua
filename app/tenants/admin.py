from django.contrib import admin

from .models import Tenant


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "slug",
        "db_name",
        "activo",
        "creado_en",
        "actualizado_en",
    )
    search_fields = ("nombre", "slug", "db_name")
    list_filter = ("activo",)
    readonly_fields = (
        "creado_en",
        "actualizado_en",
    )

    fieldsets = (
        ("Datos principales", {
            "fields": (
                "nombre",
                "slug",
                "db_name",
                "activo",
            )
        }),
        ("Auditoria", {
            "fields": (
                "creado_en",
                "actualizado_en",
            )
        }),
    )
