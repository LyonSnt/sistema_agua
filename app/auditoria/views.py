from openpyxl import Workbook

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date

from usuarios.decoradores import rol_requerido

from .models import Auditoria


def obtener_auditorias_filtradas(request):
    accion = request.GET.get("accion", "")
    modulo = request.GET.get("modulo", "")
    usuario = request.GET.get("usuario", "")
    busqueda = request.GET.get("q", "")
    fecha = request.GET.get("fecha", "")

    auditorias = Auditoria.objects.select_related("usuario").all()

    if accion:
        auditorias = auditorias.filter(accion=accion)

    if modulo:
        auditorias = auditorias.filter(modulo=modulo)

    if usuario:
        auditorias = auditorias.filter(usuario__username__icontains=usuario)

    if busqueda:
        auditorias = (
            auditorias.filter(descripcion__icontains=busqueda)
            | auditorias.filter(objeto_repr__icontains=busqueda)
        )

    fecha_parseada = parse_date(fecha) if fecha else None
    if fecha_parseada:
        auditorias = auditorias.filter(creado_en__date=fecha_parseada)

    filtros = {
        "accion": accion,
        "modulo": modulo,
        "usuario": usuario,
        "busqueda": busqueda,
        "fecha": fecha,
    }

    return auditorias, filtros


@rol_requerido("Administrador")
def lista_auditoria(request):
    auditorias, filtros = obtener_auditorias_filtradas(request)

    modulos = (
        Auditoria.objects.exclude(modulo="")
        .order_by("modulo")
        .values_list("modulo", flat=True)
        .distinct()
    )

    paginator = Paginator(auditorias, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(request, "auditoria/lista.html", {
        "auditorias": page_obj,
        "page_obj": page_obj,
        "acciones": Auditoria.ACCIONES,
        "modulos": modulos,
        "filtros": filtros,
        "querystring": querystring.urlencode(),
    })


@rol_requerido("Administrador")
def exportar_auditoria_excel(request):
    auditorias, _ = obtener_auditorias_filtradas(request)

    wb = Workbook()
    ws = wb.active
    ws.title = "Auditoria"

    ws.append([
        "Fecha",
        "Usuario",
        "Acción",
        "Módulo",
        "Objeto",
        "Descripción",
        "IP",
        "User agent",
    ])

    for auditoria in auditorias:
        ws.append([
            timezone.localtime(auditoria.creado_en).strftime("%d/%m/%Y %H:%M"),
            auditoria.usuario.username if auditoria.usuario else "",
            auditoria.get_accion_display(),
            auditoria.modulo,
            auditoria.objeto_repr,
            auditoria.descripcion,
            str(auditoria.ip or ""),
            auditoria.user_agent,
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="auditoria.xlsx"'

    wb.save(response)
    return response
