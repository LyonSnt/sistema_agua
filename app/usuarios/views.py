from django.contrib.auth.views import LoginView, LogoutView
from auditoria.utils import registrar_auditoria
from configuracion_institucional.utils import obtener_configuracion
from django.contrib import messages
from django.shortcuts import render


def contexto_login_institucion(request):
    configuracion = obtener_configuracion()
    tenant = getattr(request, "tenant", None)

    nombre_corto = "Sistema de Agua"
    nombre_completo = "Junta administradora de agua potable"

    if configuracion and configuracion.nombre:
        nombre_completo = configuracion.nombre

    if configuracion and configuracion.nombre_corto:
        nombre_corto = configuracion.nombre_corto
    elif tenant:
        nombre_corto = tenant.nombre
    elif configuracion and configuracion.nombre:
        nombre_corto = configuracion.nombre

    nombre_display = nombre_completo

    if (
        nombre_corto
        and nombre_corto != nombre_completo
        and not nombre_completo.lower().endswith(nombre_corto.lower())
    ):
        nombre_display = f"{nombre_completo} {nombre_corto}"

    return {
        "configuracion_institucional": configuracion,
        "institucion_nombre": nombre_corto,
        "institucion_nombre_completo": nombre_completo,
        "institucion_nombre_display": nombre_display,
    }


class LoginAuditoriaView(LoginView):
    template_name = "usuarios/login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(contexto_login_institucion(self.request))
        return context

    def form_valid(self, form):
        response = super().form_valid(form)

        registrar_auditoria(
            self.request,
            accion="LOGIN",
            modulo="Autenticación",
            descripcion=f"Inicio de sesión de {self.request.user.username}",
        )

        messages.success(
            self.request,
            f"Bienvenido {self.request.user.username}"
        )

        return response

    def form_invalid(self, form):

        messages.error(
            self.request,
            "Usuario o contraseña incorrectos."
        )

        return super().form_invalid(form)


class LogoutAuditoriaView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            registrar_auditoria(
                request,
                accion="LOGOUT",
                modulo="Autenticación",
                descripcion=f"Cierre de sesión de {request.user.username}",
            )

        return super().dispatch(request, *args, **kwargs)


def axes_lockout_response(request, credentials, *args, **kwargs):
    messages.warning(
        request,
        "Por motivos de seguridad, su cuenta ha sido bloqueada temporalmente tras múltiples intentos fallidos de acceso. Intente nuevamente en 15 minutos."
    )

    return render(
        request,
        "usuarios/login.html",
        {
            "axes_locked": True,
            **contexto_login_institucion(request),
        },
        status=403
    )
