from django.contrib import admin

from .models import Auditoria


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = (
        "creado_en",
        "usuario",
        "accion",
        "modulo",
        "objeto_repr",
        "ip",
    )

    search_fields = (
        "usuario__username",
        "accion",
        "modulo",
        "descripcion",
        "objeto_repr",
    )

    list_filter = (
        "accion",
        "modulo",
        "creado_en",
    )

    readonly_fields = (
        "usuario",
        "accion",
        "modulo",
        "descripcion",
        "objeto_id",
        "objeto_repr",
        "ip",
        "user_agent",
        "creado_en",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


