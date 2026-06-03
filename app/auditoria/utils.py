from .models import Auditoria


def obtener_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    x_real_ip = request.META.get("HTTP_X_REAL_IP")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if x_real_ip:
        return x_real_ip.strip()

    return request.META.get("REMOTE_ADDR")


def registrar_auditoria(
    request,
    accion,
    modulo,
    descripcion,
    objeto=None,
):
    usuario = request.user if request.user.is_authenticated else None
    
    # print("REMOTE_ADDR:", request.META.get("REMOTE_ADDR"))
    # print("HTTP_X_FORWARDED_FOR:", request.META.get("HTTP_X_FORWARDED_FOR"))
    # print("HTTP_X_REAL_IP:", request.META.get("HTTP_X_REAL_IP"))

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