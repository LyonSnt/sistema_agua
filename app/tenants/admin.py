from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import quote, unquote
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path, reverse
from django.utils.html import format_html

from usuarios.models import Usuario

from .database import configurar_base_tenant
from .modules import TENANT_MODULES, normalizar_modulos
from .models import Tenant


class TenantAdminForm(forms.ModelForm):
    modulos_habilitados = forms.MultipleChoiceField(
        choices=TENANT_MODULES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Modulos habilitados",
        help_text="Seleccione las pestanas y funcionalidades activas para esta junta.",
    )

    class Meta:
        model = Tenant
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk:
            self.initial["modulos_habilitados"] = normalizar_modulos(
                self.instance.modulos_habilitados
            )

    def clean_modulos_habilitados(self):
        return normalizar_modulos(self.cleaned_data["modulos_habilitados"])


class TenantAdminPasswordResetForm(forms.Form):
    username = forms.CharField(
        label="Usuario administrador",
        max_length=150,
        help_text="Usuario existente dentro de la base de esta junta.",
    )
    password = forms.CharField(
        label="Nueva clave",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    password_confirm = forms.CharField(
        label="Confirmar nueva clave",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, tenant=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tenant = tenant

        if tenant:
            self.fields["username"].initial = f"admin_{tenant.slug.replace('-', '_')}"

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Las claves no coinciden.")

        if password:
            try:
                validate_password(password)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned_data


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    form = TenantAdminForm
    list_display = (
        "nombre",
        "slug",
        "db_name",
        "activo",
        "modulos_resumen",
        "creado_en",
        "actualizado_en",
    )
    search_fields = ("nombre", "slug", "db_name")
    list_filter = ("activo",)
    readonly_fields = (
        "resetear_clave_admin",
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
                "modulos_habilitados",
                "resetear_clave_admin",
            )
        }),
        ("Auditoria", {
            "fields": (
                "creado_en",
                "actualizado_en",
            )
        }),
    )

    def modulos_resumen(self, obj):
        modulos = normalizar_modulos(obj.modulos_habilitados)

        if len(modulos) == len(TENANT_MODULES):
            return "Todos"

        return ", ".join(modulos)

    modulos_resumen.short_description = "Modulos"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "<path:object_id>/reset-admin-password/",
                self.admin_site.admin_view(self.reset_admin_password_view),
                name="tenants_tenant_reset_admin_password",
            ),
        ]
        return custom_urls + urls

    def resetear_clave_admin(self, obj):
        if not obj.pk:
            return "Guarde el tenant antes de resetear claves."

        url = reverse(
            "admin:tenants_tenant_reset_admin_password",
            args=[quote(obj.pk)],
        )
        return format_html('<a class="button" href="{}">Resetear clave admin tenant</a>', url)

    resetear_clave_admin.short_description = "Clave admin tenant"

    def reset_admin_password_view(self, request, object_id):
        tenant = get_object_or_404(Tenant.objects.using("master"), pk=unquote(object_id))

        if request.method == "POST":
            form = TenantAdminPasswordResetForm(request.POST, tenant=tenant)

            if form.is_valid():
                alias = configurar_base_tenant(tenant)
                username = form.cleaned_data["username"]

                try:
                    usuario = Usuario.objects.using(alias).get(username=username)
                except Usuario.DoesNotExist:
                    form.add_error(
                        "username",
                        "No existe un usuario con ese nombre en la base de esta junta.",
                    )
                else:
                    usuario.set_password(form.cleaned_data["password"])
                    usuario.is_staff = True
                    usuario.is_superuser = True
                    usuario.is_active = True
                    usuario.save(using=alias)
                    messages.success(
                        request,
                        f"Clave actualizada para {username} en {tenant.nombre}.",
                    )
                    return redirect(
                        reverse(
                            "admin:tenants_tenant_change",
                            args=[quote(tenant.pk)],
                        )
                    )
        else:
            form = TenantAdminPasswordResetForm(tenant=tenant)

        context = {
            **self.admin_site.each_context(request),
            "title": f"Resetear clave admin tenant: {tenant.nombre}",
            "opts": self.model._meta,
            "original": tenant,
            "tenant": tenant,
            "form": form,
        }
        return render(request, "admin/tenants/reset_admin_password.html", context)

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
