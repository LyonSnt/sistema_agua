from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.views.decorators.http import require_http_methods
from django.shortcuts import get_object_or_404, redirect, render

from facturacion.models import Factura
from .models import Pago
from django.utils import timezone
from usuarios.decoradores import rol_requerido
from auditoria.utils import registrar_auditoria

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.urls import reverse


@rol_requerido("Administrador", "Supervisor", "Cajero")
@require_http_methods(["GET", "POST"])
def cobrar_factura(request, factura_id):
    factura = get_object_or_404(
        Factura,
        id=factura_id,
        estado__in=["PENDIENTE", "PARCIAL"],
        activo=True,
    )

    if request.method == "POST":
        metodo_pago = request.POST.get("metodo_pago", "EFECTIVO")
        referencia = request.POST.get("referencia", "")
        observacion = request.POST.get("observacion", "")
        valor_recibido = request.POST.get("valor_pagado", "0")

        try:
            valor_pagado = Decimal(valor_recibido)

            if not valor_pagado.is_finite():
                raise InvalidOperation

        except (InvalidOperation, TypeError):
            messages.error(
                request,
                "Ingrese un valor de pago válido."
            )
            return render(request, "pagos/cobrar.html", {
                "factura": factura,
            })

        try:
            pago = Pago.objects.create(
                factura=factura,
                metodo_pago=metodo_pago,
                valor_pagado=valor_pagado,
                referencia=referencia,
                observacion=observacion,
                creado_por=request.user,
                actualizado_por=request.user,
            )
        except ValidationError as exc:
            for error in exc.messages:
                messages.error(request, error)

            return render(request, "pagos/cobrar.html", {
                "factura": factura,
            })

        registrar_auditoria(
            request,
            accion="PAGO",
            modulo="Pagos",
            descripcion=f"Registró pago de ${pago.valor_pagado} para la factura {pago.factura.numero}",
            objeto=pago,
        )

        messages.success(request, "Pago registrado correctamente.")
        return redirect("pagos:pago_exitoso", pago_id=pago.id)
    
    return render(request, "pagos/cobrar.html", {
        "factura": factura,
    })

@rol_requerido("Administrador", "Supervisor", "Cajero")
def comprobante_pago(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related(
            "factura",
            "factura__abonado",
            "factura__periodo",
        ),
        id=pago_id,
        activo=True,
    )

    return render(request, "pagos/comprobante.html", {
        "pago": pago,
    })

@rol_requerido("Administrador")
@require_http_methods(["GET", "POST"])
def anular_pago(request, pago_id):
    pago = get_object_or_404(
        Pago,
        id=pago_id,
        activo=True,
        anulado=False,
    )

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()

        if not motivo:
            messages.error(
                request,
                "Debe ingresar el motivo de anulación."
            )

            return redirect(
                "pagos:anular",
                pago_id=pago.id
            )

        pago.anulado = True
        pago.fecha_anulacion = timezone.now()
        pago.motivo_anulacion = motivo
        pago.actualizado_por = request.user

        pago.save()

        pago.factura.actualizar_estado_pago()
        
        registrar_auditoria(
            request,
            accion="ANULAR_PAGO",
            modulo="Pagos",
            descripcion=(
                f"Anuló el pago de ${pago.valor_pagado} "
                f"de la factura {pago.factura.numero}. "
                f"Motivo: {pago.motivo_anulacion}"
            ),
            objeto=pago,
        )

        messages.success(
            request,
            "Pago anulado correctamente."
        )

        return redirect(
            "reportes:facturas_pagadas"
        )

    return render(
        request,
        "pagos/anular.html",
        {
            "pago": pago
        }
    )

@rol_requerido("Administrador", "Supervisor", "Cajero")
def comprobante_pago_pdf(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related(
            "factura",
            "factura__abonado",
            "creado_por",
        ),
        id=pago_id,
        activo=True,
    )

    html_string = render_to_string(
        "pagos/pdf_comprobante_pago.html",
        {
            "pago": pago,
            "factura": pago.factura,
        }
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")

    response["Content-Disposition"] = (
        f'inline; filename="comprobante_pago_{pago.factura.numero}.pdf"'
    )

    return response


@rol_requerido("Administrador", "Supervisor", "Cajero")
def pago_exitoso(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related("factura", "factura__abonado"),
        id=pago_id,
        activo=True,
    )

    return render(request, "pagos/exitoso.html", {
        "pago": pago,
        "factura": pago.factura,
    })


@rol_requerido("Administrador", "Supervisor", "Cajero")
def comprobante_pago_imprimir(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related(
            "factura",
            "factura__abonado",
            "creado_por",
        ),
        id=pago_id,
        activo=True,
    )

    return render(request, "pagos/imprimir_comprobante.html", {
        "pago": pago,
        "factura": pago.factura,
    })


@rol_requerido("Administrador", "Supervisor", "Cajero")
def ticket_pago(request, pago_id):
    pago = get_object_or_404(
        Pago.objects.select_related(
            "factura",
            "factura__abonado",
            "creado_por",
        ).prefetch_related(
            "factura__detalles"
        ),
        id=pago_id,
        activo=True,
    )

    return render(request, "pagos/ticket_pago.html", {
        "pago": pago,
        "factura": pago.factura,
    })
