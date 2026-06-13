from .models import ConfiguracionInstitucional


def obtener_configuracion():
    return ConfiguracionInstitucional.objects.first()


def obtener_contexto_institucion(request):
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
