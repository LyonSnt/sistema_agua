from copy import deepcopy

from django.urls import reverse

from usuarios.context_processors import roles_usuario

from .menu import MENU_SIDEBAR


def _ruta_sin_prefijo_tenant(request):
    ruta = request.path
    prefijo = getattr(request, "tenant_path_prefix", "")

    if prefijo and ruta.startswith(f"{prefijo}/"):
        return ruta[len(prefijo):]

    return ruta


def _url_tenant(request, viewname):
    url = reverse(viewname)
    prefijo = getattr(request, "tenant_path_prefix", "")

    if not prefijo or url.startswith(f"{prefijo}/") or url == prefijo:
        return url

    return f"{prefijo}{url}"


def _tiene_permiso(contexto, item):
    permiso = item.get("permiso")
    permiso_extra = item.get("permiso_extra")

    if permiso and not contexto.get(permiso):
        return False

    if permiso_extra and not contexto.get(permiso_extra):
        return False

    return True


def _esta_activo(ruta, item):
    rutas_activas = item.get("rutas_activas", [])
    rutas_excluidas = item.get("rutas_excluidas", [])

    if any(ruta.startswith(ruta_excluida) for ruta_excluida in rutas_excluidas):
        return False

    return any(ruta.startswith(ruta_activa) for ruta_activa in rutas_activas)


def construir_menu_sidebar(request, contexto=None):
    contexto = contexto or {}
    ruta = _ruta_sin_prefijo_tenant(request)
    secciones = []

    for seccion in MENU_SIDEBAR:
        items = []

        for item_config in seccion["items"]:
            if not _tiene_permiso(contexto, item_config):
                continue

            item = deepcopy(item_config)
            item["url"] = _url_tenant(request, item["url_name"])
            item["activo"] = _esta_activo(ruta, item)
            items.append(item)

        if items:
            secciones.append({
                "titulo": seccion["titulo"],
                "items": items,
            })

    return secciones


def menu_sidebar(request):
    if not request.user.is_authenticated:
        return {"menu_sidebar": []}

    return {
        "menu_sidebar": construir_menu_sidebar(
            request,
            contexto=roles_usuario(request),
        )
    }
