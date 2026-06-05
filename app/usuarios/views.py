from django.contrib.auth.views import LoginView, LogoutView
from auditoria.utils import registrar_auditoria
from django.contrib import messages
from django.shortcuts import render

class LoginAuditoriaView(LoginView):
    template_name = "usuarios/login.html"

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
            "axes_locked": True
        },
        status=403
    )