from .models import Auditoria


def obtener_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]

    return request.META.get("REMOTE_ADDR")


def registrar_auditoria(
    request,
    accion,
    modulo,
    descripcion,
    objeto=None,
):
    usuario = request.user if request.user.is_authenticated else None

    Auditoria.objects.create(
        usuario=usuario,
        accion=accion,
        modulo=modulo,
        descripcion=descripcion,
        objeto_id=str(objeto.pk) if objeto else "",
        objeto_repr=str(objeto) if objeto else "",
        ip=obtener_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )