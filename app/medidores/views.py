from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from usuarios.decoradores import rol_requerido
from facturacion.models import Factura
from .models import Medidor

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from configuracion_institucional.utils import obtener_configuracion

from django.contrib import messages
from django.shortcuts import redirect
from auditoria.utils import registrar_auditoria
from .forms import MedidorForm


@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def lista_medidores(request):
    busqueda = request.GET.get("q", "")

    medidores = Medidor.objects.select_related(
        "abonado",
        "abonado__sector",
        "abonado__ruta",
    ).filter(
        activo=True
    ).order_by("numero")

    if busqueda:
        medidores = (
            medidores.filter(numero__icontains=busqueda)
            | medidores.filter(abonado__nombres__icontains=busqueda)
            | medidores.filter(abonado__apellidos__icontains=busqueda)
            | medidores.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    paginator = Paginator(medidores, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "medidores/lista_medidores.html", {
        "medidores": page_obj,
        "page_obj": page_obj,
        "busqueda": busqueda,
        "querystring": f"q={busqueda}",
    })


@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def detalle_medidor(request, medidor_id):
    medidor = get_object_or_404(
        Medidor.objects.select_related(
            "abonado",
            "abonado__sector",
            "abonado__ruta",
        ),
        id=medidor_id,
        activo=True
    )

    lecturas = medidor.lecturas.select_related(
        "periodo"
    ).filter(
        activo=True
    ).order_by("-periodo__anio", "-periodo__mes")

    ultima_lectura = lecturas.first()

    facturas = Factura.objects.select_related(
        "periodo",
        "abonado",
    ).filter(
        lectura__medidor=medidor,
        activo=True,
    ).order_by("-fecha_emision", "-numero")

    total_lecturas = lecturas.count()
    total_facturas = facturas.count()

    consumo_acumulado = sum(l.consumo for l in lecturas)

    facturas_pendientes = facturas.filter(
        estado__in=["PENDIENTE", "PARCIAL"]
    ).count()

    return render(request, "medidores/detalle_medidor.html", {
        "medidor": medidor,
        "lecturas": lecturas,
        "ultima_lectura": ultima_lectura,
        "facturas": facturas,
        "total_lecturas": total_lecturas,
        "total_facturas": total_facturas,
        "consumo_acumulado": consumo_acumulado,
        "facturas_pendientes": facturas_pendientes,
    })



@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def detalle_medidor_pdf(request, medidor_id):
    medidor = get_object_or_404(
        Medidor.objects.select_related(
            "abonado",
            "abonado__sector",
            "abonado__ruta",
        ),
        id=medidor_id,
        activo=True
    )

    lecturas = medidor.lecturas.select_related(
        "periodo"
    ).filter(
        activo=True
    ).order_by("-periodo__anio", "-periodo__mes")

    ultima_lectura = lecturas.first()

    facturas = Factura.objects.select_related(
        "periodo",
        "abonado",
    ).filter(
        lectura__medidor=medidor,
        activo=True,
    ).order_by("-fecha_emision", "-numero")

    total_lecturas = lecturas.count()
    total_facturas = facturas.count()
    consumo_acumulado = sum(l.consumo for l in lecturas)

    facturas_pendientes = facturas.filter(
        estado__in=["PENDIENTE", "PARCIAL"]
    ).count()

    html_string = render_to_string(
        "medidores/detalle_medidor_pdf.html",
        {
            "configuracion": obtener_configuracion(),
            "medidor": medidor,
            "lecturas": lecturas,
            "ultima_lectura": ultima_lectura,
            "facturas": facturas,
            "total_lecturas": total_lecturas,
            "total_facturas": total_facturas,
            "consumo_acumulado": consumo_acumulado,
            "facturas_pendientes": facturas_pendientes,
        }
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="ficha_medidor_{medidor.numero}.pdf"'
    )

    return response


@rol_requerido("Administrador", "Supervisor")
def crear_medidor(request):
    if request.method == "POST":
        form = MedidorForm(request.POST)

        if form.is_valid():
            medidor = form.save(commit=False)
            medidor.creado_por = request.user
            medidor.actualizado_por = request.user
            medidor.save()

            registrar_auditoria(
                request,
                accion="CREAR_MEDIDOR",
                modulo="Medidores",
                descripcion=f"Creó el medidor {medidor.numero} para {medidor.abonado}",
                objeto=medidor,
            )

            messages.success(request, "Medidor creado correctamente.")
            return redirect("medidores:detalle", medidor_id=medidor.id)
    else:
        form = MedidorForm()

    return render(request, "medidores/form_medidor.html", {
        "form": form,
        "titulo": "Crear medidor",
        "boton": "Guardar medidor",
    })


@rol_requerido("Administrador", "Supervisor")
def editar_medidor(request, medidor_id):
    medidor = get_object_or_404(
        Medidor,
        id=medidor_id,
        activo=True
    )

    if request.method == "POST":
        form = MedidorForm(request.POST, instance=medidor)

        if form.is_valid():
            medidor = form.save(commit=False)
            medidor.actualizado_por = request.user
            medidor.save()

            registrar_auditoria(
                request,
                accion="EDITAR_MEDIDOR",
                modulo="Medidores",
                descripcion=f"Editó el medidor {medidor.numero}",
                objeto=medidor,
            )

            messages.success(request, "Medidor actualizado correctamente.")
            return redirect("medidores:detalle", medidor_id=medidor.id)
    else:
        form = MedidorForm(instance=medidor)

    return render(request, "medidores/form_medidor.html", {
        "form": form,
        "medidor": medidor,
        "titulo": "Editar medidor",
        "boton": "Actualizar medidor",
    })




