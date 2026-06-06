from django.core.paginator import Paginator
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from weasyprint import HTML

from auditoria.models import Auditoria
from auditoria.utils import registrar_auditoria
from configuracion_institucional.utils import obtener_configuracion
from medidores.models import CambioMedidor
from multas.models import Multa
from pagos.models import Pago
from usuarios.decoradores import rol_requerido

from .forms import AbonadoForm
from .models import Abonado


@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def lista_abonados(request):
    busqueda = request.GET.get("q", "")

    abonados = Abonado.objects.select_related("sector", "ruta").filter(activo=True)

    if busqueda:
        abonados = abonados.filter(
            nombres__icontains=busqueda
        ) | abonados.filter(
            apellidos__icontains=busqueda
        ) | abonados.filter(
            cedula_ruc__icontains=busqueda
        ) | abonados.filter(
            codigo__icontains=busqueda
        )

    paginator = Paginator(abonados, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    contexto = {
        "abonados": page_obj,
        "page_obj": page_obj,
        "busqueda": busqueda,
        "querystring": f"q={busqueda}",
    }

    return render(request, "abonados/lista_abonados.html", contexto)


@rol_requerido("Administrador", "Supervisor")
def crear_abonado(request):
    if request.method == "POST":
        form = AbonadoForm(request.POST)

        if form.is_valid():
            abonado = form.save(commit=False)
            abonado.creado_por = request.user
            abonado.actualizado_por = request.user
            abonado.save()

            registrar_auditoria(
                request,
                accion="CREAR",
                modulo="Abonados",
                descripcion=f"Creó el abonado {abonado}",
                objeto=abonado,
            )

            messages.success(request, "Abonado creado correctamente.")
            return redirect("abonados:detalle", abonado_id=abonado.id)
    else:
        form = AbonadoForm()

    return render(request, "abonados/form_abonado.html", {
        "form": form,
        "titulo": "Crear abonado",
        "boton": "Guardar abonado",
    })


@rol_requerido("Administrador", "Supervisor")
def editar_abonado(request, abonado_id):
    abonado = get_object_or_404(Abonado, id=abonado_id)

    if request.method == "POST":
        form = AbonadoForm(request.POST, instance=abonado)

        if form.is_valid():
            abonado = form.save(commit=False)
            abonado.actualizado_por = request.user
            abonado.save()

            registrar_auditoria(
                request,
                accion="ACTUALIZAR",
                modulo="Abonados",
                descripcion=f"Actualizó el abonado {abonado}",
                objeto=abonado,
            )

            messages.success(request, "Abonado actualizado correctamente.")
            return redirect("abonados:detalle", abonado_id=abonado.id)
    else:
        form = AbonadoForm(instance=abonado)

    return render(request, "abonados/form_abonado.html", {
        "form": form,
        "abonado": abonado,
        "titulo": "Editar abonado",
        "boton": "Guardar cambios",
    })


def obtener_contexto_ficha_abonado(abonado_id):
    abonado = get_object_or_404(
        Abonado.objects.select_related("sector", "ruta"),
        id=abonado_id,
        activo=True
    )

    facturas = abonado.facturas.select_related(
        "periodo"
    ).prefetch_related(
        "pagos",
        "detalles"
    ).order_by("-fecha_emision", "-numero")

    total_facturado = sum(f.total for f in facturas)
    total_pagado = sum(f.total_pagado for f in facturas)
    saldo_pendiente = sum(f.saldo_pendiente for f in facturas)

    historial_suspensiones = abonado.suspensiones.filter(
        activo=True
    ).order_by("-fecha_suspension")

    facturas_pendientes = facturas.filter(
        estado__in=["PENDIENTE", "PARCIAL"]
    ).count()

    facturas_pagadas = facturas.filter(
        estado="PAGADA"
    ).count()

    pagos = Pago.objects.select_related(
        "factura"
    ).filter(
        factura__abonado=abonado,
        activo=True
    ).order_by("-fecha_pago")

    medidores = abonado.medidores.filter(
        activo=True
    ).order_by("estado", "numero")

    medidor = medidores.exclude(
        estado="RETIRADO"
    ).first() or medidores.first()

    ultima_lectura = None

    if medidor:
        ultima_lectura = medidor.lecturas.order_by(
            "-periodo__anio",
            "-periodo__mes"
        ).first()

    factura_pendiente = facturas.filter(
        estado__in=["PENDIENTE", "PARCIAL"]
    ).order_by("fecha_emision").first()

    cambios_medidor = CambioMedidor.objects.select_related(
        "medidor_anterior",
        "medidor_nuevo",
        "creado_por",
    ).filter(
        abonado=abonado,
        activo=True,
    ).order_by("-fecha_cambio", "-id")

    multas = Multa.objects.filter(
        abonado=abonado,
        activo=True,
    ).order_by("-fecha", "-id")

    total_multas = sum(multa.valor for multa in multas)
    multas_pendientes = multas.filter(estado="PENDIENTE").count()

    auditorias = Auditoria.objects.select_related("usuario").filter(
        objeto_repr__icontains=str(abonado)
    ).order_by("-creado_en")[:10]

    return {
        "abonado": abonado,
        "facturas": facturas,
        "pagos": pagos,
        "medidores": medidores,
        "medidor": medidor,
        "ultima_lectura": ultima_lectura,
        "total_facturado": total_facturado,
        "total_pagado": total_pagado,
        "saldo_pendiente": saldo_pendiente,
        "facturas_pendientes": facturas_pendientes,
        "facturas_pagadas": facturas_pagadas,
        "historial_suspensiones": historial_suspensiones,
        "factura_pendiente": factura_pendiente,
        "cambios_medidor": cambios_medidor,
        "multas": multas,
        "total_multas": total_multas,
        "multas_pendientes": multas_pendientes,
        "auditorias": auditorias,
    }


@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def detalle_abonado(request, abonado_id):
    contexto = obtener_contexto_ficha_abonado(abonado_id)

    return render(
        request,
        "abonados/detalle_abonado.html",
        contexto
    )


@rol_requerido("Administrador", "Supervisor", "Cajero", "Lecturista", "Consulta")
def detalle_abonado_pdf(request, abonado_id):
    contexto = obtener_contexto_ficha_abonado(abonado_id)
    contexto["configuracion"] = obtener_configuracion()

    html_string = render_to_string(
        "abonados/detalle_abonado_pdf.html",
        contexto
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="ficha_abonado_{contexto["abonado"].codigo}.pdf"'
    )

    registrar_auditoria(
        request,
        accion="EXPORTAR_REPORTE",
        modulo="Abonados",
        descripcion=f"Descargó ficha PDF del abonado {contexto['abonado']}",
        objeto=contexto["abonado"],
    )

    return response












