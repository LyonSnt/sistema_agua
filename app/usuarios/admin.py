from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Información adicional", {
            "fields": ("telefono", "cargo", "debe_cambiar_clave"),
        }),
    )

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "telefono",
        "cargo",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "telefono",
    )