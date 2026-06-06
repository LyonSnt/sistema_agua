from datetime import date

from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from usuarios.decoradores import rol_requerido
from facturacion.models import Factura
from .models import CambioMedidor, Medidor

from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
from configuracion_institucional.utils import obtener_configuracion

from django.contrib import messages
from django.shortcuts import redirect
from auditoria.utils import registrar_auditoria
from .forms import CambioMedidorForm, MedidorForm


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

    cambios = CambioMedidor.objects.select_related(
        "medidor_anterior",
        "medidor_nuevo",
        "creado_por",
    ).filter(
        activo=True,
        abonado=medidor.abonado,
    ).filter(
        medidor_anterior=medidor
    ) | CambioMedidor.objects.select_related(
        "medidor_anterior",
        "medidor_nuevo",
        "creado_por",
    ).filter(
        activo=True,
        abonado=medidor.abonado,
        medidor_nuevo=medidor,
    )
    cambios = cambios.order_by("-fecha_cambio", "-id")

    return render(request, "medidores/detalle_medidor.html", {
        "medidor": medidor,
        "lecturas": lecturas,
        "ultima_lectura": ultima_lectura,
        "facturas": facturas,
        "total_lecturas": total_lecturas,
        "total_facturas": total_facturas,
        "consumo_acumulado": consumo_acumulado,
        "facturas_pendientes": facturas_pendientes,
        "cambios": cambios,
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


@rol_requerido("Administrador", "Supervisor")
@require_http_methods(["GET", "POST"])
def cambiar_medidor(request, medidor_id):
    medidor_anterior = get_object_or_404(
        Medidor.objects.select_related("abonado"),
        id=medidor_id,
        activo=True,
    )

    if medidor_anterior.estado == "RETIRADO":
        messages.error(
            request,
            "No se puede cambiar un medidor que ya fue retirado."
        )
        return redirect("medidores:detalle", medidor_id=medidor_anterior.id)

    if request.method == "POST":
        form = CambioMedidorForm(
            request.POST,
            medidor_anterior=medidor_anterior,
        )

        if form.is_valid():
            with transaction.atomic():
                medidor_nuevo = Medidor.objects.create(
                    abonado=medidor_anterior.abonado,
                    numero=form.cleaned_data["numero_nuevo"],
                    marca=form.cleaned_data["marca_nuevo"],
                    modelo=form.cleaned_data["modelo_nuevo"],
                    lectura_inicial=form.cleaned_data["lectura_inicial_nuevo"],
                    fecha_instalacion=form.cleaned_data["fecha_cambio"],
                    estado="ACTIVO",
                    creado_por=request.user,
                    actualizado_por=request.user,
                )

                cambio = CambioMedidor.objects.create(
                    abonado=medidor_anterior.abonado,
                    medidor_anterior=medidor_anterior,
                    medidor_nuevo=medidor_nuevo,
                    fecha_cambio=form.cleaned_data["fecha_cambio"],
                    lectura_final_anterior=form.cleaned_data["lectura_final_anterior"],
                    lectura_inicial_nuevo=form.cleaned_data["lectura_inicial_nuevo"],
                    motivo=form.cleaned_data["motivo"],
                    creado_por=request.user,
                    actualizado_por=request.user,
                )

                medidor_anterior.estado = "RETIRADO"
                medidor_anterior.actualizado_por = request.user
                medidor_anterior.save(update_fields=[
                    "estado",
                    "actualizado_por",
                    "actualizado_en",
                ])

            registrar_auditoria(
                request,
                accion="CAMBIAR_MEDIDOR",
                modulo="Medidores",
                descripcion=(
                    f"Cambió el medidor {medidor_anterior.numero} "
                    f"por {medidor_nuevo.numero} para {medidor_anterior.abonado}"
                ),
                objeto=cambio,
            )

            messages.success(request, "Cambio de medidor registrado correctamente.")
            return redirect("medidores:detalle", medidor_id=medidor_nuevo.id)

        messages.error(request, "Revise los datos ingresados.")
    else:
        form = CambioMedidorForm(
            initial={"fecha_cambio": date.today()},
            medidor_anterior=medidor_anterior,
        )

    return render(request, "medidores/cambiar_medidor.html", {
        "form": form,
        "medidor": medidor_anterior,
    })


