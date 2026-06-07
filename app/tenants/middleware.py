from urllib.parse import urlparse

from django.conf import settings
from django.http import Http404
from django.http import HttpResponseRedirect

from tenants.context import activar_tenant_db, limpiar_tenant_db
from tenants.database import configurar_base_tenant
from tenants.models import Tenant


class TenantPathMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = activar_tenant_db("")

        try:
            redirect_legacy = self._redireccionar_legacy_desde_referer_tenant(request)

            if redirect_legacy:
                return redirect_legacy

            alias = self._resolver_tenant(request)
            limpiar_tenant_db(token)
            token = activar_tenant_db(alias)
            response = self.get_response(request)
            self._prefijar_redirect_tenant(request, response)
            return response
        finally:
            limpiar_tenant_db(token)

    def _resolver_tenant(self, request):
        request.tenant = None
        request.tenant_slug = ""
        request.tenant_db_alias = ""
        request.tenant_path_prefix = ""

        if settings.TENANT_ROUTE_MODE != "path":
            return ""

        segmentos = [segmento for segmento in request.path_info.split("/") if segmento]

        if not segmentos:
            return ""

        slug = segmentos[0].lower()

        if slug not in settings.TENANT_SLUGS:
            return ""

        try:
            tenant = Tenant.objects.using("master").get(slug=slug, activo=True)
        except Tenant.DoesNotExist as exc:
            raise Http404("Tenant no encontrado.") from exc

        request.tenant = tenant
        request.tenant_slug = tenant.slug
        request.tenant_db_alias = configurar_base_tenant(tenant)
        request.tenant_path_prefix = f"/{tenant.slug}"

        ruta_interna = request.path_info[len(request.tenant_path_prefix):] or "/"

        if not ruta_interna.startswith("/"):
            ruta_interna = f"/{ruta_interna}"

        request.path_info = ruta_interna
        return request.tenant_db_alias

    def _redireccionar_legacy_desde_referer_tenant(self, request):
        if settings.TENANT_ROUTE_MODE != "path":
            return None

        if request.method not in ("GET", "HEAD"):
            return None

        segmentos = [segmento for segmento in request.path_info.split("/") if segmento]

        if segmentos and segmentos[0].lower() in settings.TENANT_SLUGS:
            return None

        referer = request.META.get("HTTP_REFERER", "")

        if not referer:
            return None

        referer_parseado = urlparse(referer)

        if referer_parseado.netloc and referer_parseado.netloc != request.get_host():
            return None

        segmentos_referer = [
            segmento
            for segmento in referer_parseado.path.split("/")
            if segmento
        ]

        if not segmentos_referer:
            return None

        slug = segmentos_referer[0].lower()

        if slug not in settings.TENANT_SLUGS:
            return None

        return HttpResponseRedirect(f"/{slug}{request.get_full_path()}")

    def _prefijar_redirect_tenant(self, request, response):
        prefijo = getattr(request, "tenant_path_prefix", "")

        if not prefijo or not response.has_header("Location"):
            return

        location = response["Location"]

        if not self._debe_prefijar_location(location, prefijo):
            return

        response["Location"] = f"{prefijo}{location}"

    def _debe_prefijar_location(self, location, prefijo):
        if not location.startswith("/") or location.startswith("//"):
            return False

        if location.startswith(f"{prefijo}/") or location == prefijo:
            return False

        return True
