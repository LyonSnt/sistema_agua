from django import template
from django.urls import reverse


register = template.Library()


@register.simple_tag(takes_context=True)
def tenant_url(context, viewname, *args, **kwargs):
    url = reverse(viewname, args=args, kwargs=kwargs)
    request = context.get("request")
    prefijo = getattr(request, "tenant_path_prefix", "") if request else ""

    if not prefijo or url.startswith(f"{prefijo}/") or url == prefijo:
        return url

    return f"{prefijo}{url}"
