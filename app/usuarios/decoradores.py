from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect


def rol_requerido(*roles_permitidos):
    def decorador(vista):
        @wraps(vista)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return vista(request, *args, **kwargs)

            pertenece = request.user.groups.filter(
                name__in=roles_permitidos
            ).exists()

            if pertenece:
                return vista(request, *args, **kwargs)

            messages.error(
                request,
                "No tiene permisos para acceder a esta opción."
            )
            return redirect("panel:inicio")

        return wrapper

    return decorador