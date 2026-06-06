from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuarios.decoradores import rol_requerido
from auditoria.utils import registrar_auditoria
from abonados.models import Abonado
from .forms import MultaForm
from .models import Multa

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from openpyxl import Workbook
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods


@rol_requerido("Administrador", "Supervisor", "Cajero")
def lista_multas(request):
    busqueda = request.GET.get("q", "")

    multas = Multa.objects.select_related("abonado").filter(
        activo=True
    ).order_by("-fecha")

    if busqueda:
        multas = (
            multas.filter(abonado__nombres__icontains=busqueda)
            | multas.filter(abonado__apellidos__icontains=busqueda)
            | multas.filter(abonado__cedula_ruc__icontains=busqueda)
            | multas.filter(motivo__icontains=busqueda)
        )
    paginator = Paginator(multas, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "multas/lista.html", {
        "multas": page_obj,
        "page_obj": page_obj,
        "busqueda": busqueda,
        "querystring": f"q={busqueda}",
    })


@rol_requerido("Administrador", "Supervisor", "Cajero")
@require_http_methods(["GET", "POST"])
def crear_multa(request):
    abonados = Abonado.objects.filter(activo=True).order_by("apellidos", "nombres")

    if request.method == "POST":
        form = MultaForm(request.POST)

        if form.is_valid():
            multa = form.save(commit=False)
            multa.creado_por = request.user
            multa.actualizado_por = request.user
            multa.save()

            registrar_auditoria(
                request,
                accion="CREAR_MULTA",
                modulo="Multas",
                descripcion=f"Registró multa para {multa.abonado} por ${multa.valor}",
                objeto=multa,
            )

            messages.success(request, "Multa registrada correctamente.")
            return redirect("multas:lista")

        messages.error(request, "Revise los datos ingresados.")
    else:
        form = MultaForm()

    return render(request, "multas/crear.html", {
        "abonados": abonados,
        "form": form,
        "tipos": Multa.TIPOS,
        "hoy": timezone.localdate(),
    })


@rol_requerido("Administrador", "Supervisor", "Cajero")
@require_http_methods(["GET", "POST"])
def cobrar_multa(request, multa_id):
    multa = get_object_or_404(
        Multa,
        id=multa_id,
        activo=True,
        estado="PENDIENTE",
    )

    if request.method == "POST":
        multa.estado = "PAGADA"
        multa.fecha_pago = timezone.now()
        multa.metodo_pago = request.POST.get("metodo_pago")
        multa.referencia = request.POST.get("referencia", "")
        multa.actualizado_por = request.user
        multa.save()

        registrar_auditoria(
            request,
            accion="COBRAR_MULTA",
            modulo="Multas",
            descripcion=f"Cobró multa de ${multa.valor} a {multa.abonado}",
            objeto=multa,
        )

        messages.success(request, "Multa cobrada correctamente.")
        return redirect("multas:lista")

    return render(request, "multas/cobrar.html", {
        "multa": multa,
    })

@rol_requerido("Administrador")
@require_http_methods(["GET", "POST"])
def anular_multa(request, multa_id):
    multa = get_object_or_404(
        Multa,
        id=multa_id,
        activo=True,
    )

    if multa.estado == "ANULADA":
        messages.error(request, "La multa ya se encuentra anulada.")
        return redirect("multas:lista")

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()

        if not motivo:
            messages.error(request, "Debe ingresar el motivo de anulación.")
            return redirect("multas:anular", multa_id=multa.id)

        multa.estado = "ANULADA"
        multa.fecha_anulacion = timezone.now()
        multa.motivo_anulacion = motivo
        multa.actualizado_por = request.user
        multa.save()

        registrar_auditoria(
            request,
            accion="ANULAR_MULTA",
            modulo="Multas",
            descripcion=f"Anuló multa de ${multa.valor} a {multa.abonado}. Motivo: {motivo}",
            objeto=multa,
        )

        messages.success(request, "Multa anulada correctamente.")
        return redirect("multas:lista")

    return render(request, "multas/anular.html", {
        "multa": multa,
    })


@rol_requerido("Administrador", "Supervisor", "Cajero")
def comprobante_multa_pdf(request, multa_id):
    multa = get_object_or_404(
        Multa.objects.select_related(
            "abonado",
            "actualizado_por",
        ),
        id=multa_id,
        activo=True,
        estado="PAGADA",
    )

    html_string = render_to_string(
        "multas/pdf_comprobante_multa.html",
        {
            "multa": multa,
        }
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="comprobante_multa_{multa.id}.pdf"'
    )

    registrar_auditoria(
        request,
        accion="EXPORTAR_REPORTE",
        modulo="Multas",
        descripcion=f"Descargó comprobante PDF de la multa {multa.id}",
        objeto=multa,
    )

    return response


@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def reporte_multas(request):
    estado = request.GET.get("estado", "")
    tipo = request.GET.get("tipo", "")
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    multas = Multa.objects.select_related("abonado").filter(
        activo=True
    ).order_by("-fecha")

    if estado:
        multas = multas.filter(estado=estado)

    if tipo:
        multas = multas.filter(tipo=tipo)

    if fecha_inicio:
        multas = multas.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        multas = multas.filter(fecha__lte=fecha_fin)

    total_multas = multas.count()
    pendientes = multas.filter(estado="PENDIENTE").count()
    pagadas = multas.filter(estado="PAGADA").count()
    anuladas = multas.filter(estado="ANULADA").count()

    total_recaudado = sum(
        multa.valor for multa in multas if multa.estado == "PAGADA"
    )

    return render(request, "multas/reporte.html", {
        "multas": multas,
        "total_multas": total_multas,
        "pendientes": pendientes,
        "pagadas": pagadas,
        "anuladas": anuladas,
        "total_recaudado": total_recaudado,
        "estado": estado,
        "tipo": tipo,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "estados": Multa.ESTADOS,
        "tipos": Multa.TIPOS,
    })

@rol_requerido("Administrador", "Supervisor")
def exportar_reporte_multas_excel(request):
    estado = request.GET.get("estado", "")
    tipo = request.GET.get("tipo", "")
    fecha_inicio = request.GET.get("fecha_inicio", "")
    fecha_fin = request.GET.get("fecha_fin", "")

    multas = Multa.objects.select_related("abonado").filter(activo=True).order_by("-fecha")

    if estado:
        multas = multas.filter(estado=estado)

    if tipo:
        multas = multas.filter(tipo=tipo)

    if fecha_inicio:
        multas = multas.filter(fecha__gte=fecha_inicio)

    if fecha_fin:
        multas = multas.filter(fecha__lte=fecha_fin)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reporte multas"

    ws.append(["REPORTE DE MULTAS"])
    ws.append(["Estado", estado or "Todos"])
    ws.append(["Tipo", tipo or "Todos"])
    ws.append(["Desde", fecha_inicio or "-"])
    ws.append(["Hasta", fecha_fin or "-"])
    ws.append([])

    ws.append([
        "Abonado",
        "Cédula/RUC",
        "Tipo",
        "Fecha",
        "Motivo",
        "Valor",
        "Estado",
        "Fecha pago",
        "Método pago",
    ])

    total_recaudado = 0

    for multa in multas:
        if multa.estado == "PAGADA":
            total_recaudado += multa.valor

        ws.append([
            str(multa.abonado),
            multa.abonado.cedula_ruc,
            multa.get_tipo_display(),
            str(multa.fecha),
            multa.motivo,
            float(multa.valor),
            multa.get_estado_display(),
            str(multa.fecha_pago) if multa.fecha_pago else "",
            multa.metodo_pago,
        ])

    ws.append([])
    ws.append(["", "", "", "", "TOTAL RECAUDADO", float(total_recaudado)])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="reporte_multas.xlsx"'

    wb.save(response)

    registrar_auditoria(
        request,
        accion="EXPORTAR_REPORTE",
        modulo="Multas",
        descripcion="Exportó reporte de multas a Excel",
    )

    return response
