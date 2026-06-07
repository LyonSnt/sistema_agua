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

    def has_module_permission(self, request):
        return not getattr(request, "tenant", None) and super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        return not getattr(request, "tenant", None) and super().has_view_permission(request, obj)

    def has_add_permission(self, request):
        return not getattr(request, "tenant", None) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return not getattr(request, "tenant", None) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return not getattr(request, "tenant", None) and super().has_delete_permission(request, obj)
