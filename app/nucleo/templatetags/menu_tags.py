from django import template

from nucleo.context_processors import construir_menu_sidebar


register = template.Library()


@register.simple_tag(takes_context=True)
def obtener_menu_sidebar(context):
    menu = context.get("menu_sidebar")
    if menu is not None:
        return menu

    request = context.get("request")
    if not request:
        return []

    return construir_menu_sidebar(request, contexto=context.flatten())
