from django.contrib.auth.views import LoginView, LogoutView
from auditoria.utils import registrar_auditoria


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

        return response


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

