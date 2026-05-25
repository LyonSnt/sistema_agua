from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from pagos.models import Pago
from facturacion.models import Factura
from usuarios.decoradores import rol_requerido


@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def cierre_diario(request):
    fecha = request.GET.get("fecha") or timezone.localdate()

    pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
    ).prefetch_related(
        "factura__detalles"
    ).filter(
        fecha_pago__date=fecha,
        activo=True,
    )

    total_recaudado = Decimal("0.00")
    total_agua = Decimal("0.00")
    total_alcantarillado = Decimal("0.00")
    total_multas = Decimal("0.00")
    total_otros = Decimal("0.00")

    for pago in pagos:
        total_recaudado += pago.valor_pagado

        factura = pago.factura

        if factura.total <= 0:
            continue

        proporcion = pago.valor_pagado / factura.total

        for detalle in factura.detalles.all():
            valor_proporcional = detalle.valor_total * proporcion

            if detalle.tipo == "AGUA":
                total_agua += valor_proporcional
            elif detalle.tipo == "ALCANTARILLADO":
                total_alcantarillado += valor_proporcional
            elif detalle.tipo == "MULTA":
                total_multas += valor_proporcional
            else:
                total_otros += valor_proporcional

    contexto = {
        "fecha": fecha,
        "pagos": pagos,
        "total_pagos": pagos.count(),
        "total_recaudado": total_recaudado,
        "total_agua": total_agua,
        "total_alcantarillado": total_alcantarillado,
        "total_multas": total_multas,
        "total_otros": total_otros,
    }

    return render(request, "reportes/cierre_diario.html", contexto)

@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def cartera_pendiente(request):
    busqueda = request.GET.get("q", "")

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
    ).filter(
        estado__in=["PENDIENTE", "PARCIAL"],
        activo=True,
    ).order_by("abonado__apellidos", "abonado__nombres")

    if busqueda:
        facturas = (
            facturas.filter(numero__icontains=busqueda)
            | facturas.filter(abonado__nombres__icontains=busqueda)
            | facturas.filter(abonado__apellidos__icontains=busqueda)
            | facturas.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    total_cartera = sum(f.saldo_pendiente for f in facturas)

    contexto = {
        "facturas": facturas,
        "busqueda": busqueda,
        "total_cartera": total_cartera,
    }

    return render(request, "reportes/cartera.html", contexto)

@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def facturas_pagadas(request):
    busqueda = request.GET.get("q", "")

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
    ).prefetch_related(
        "pagos"
    ).filter(
        estado="PAGADA",
        activo=True,
    ).order_by("-fecha_emision")

    if busqueda:
        facturas = (
            facturas.filter(numero__icontains=busqueda)
            | facturas.filter(abonado__nombres__icontains=busqueda)
            | facturas.filter(abonado__apellidos__icontains=busqueda)
            | facturas.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    contexto = {
        "facturas": facturas,
        "busqueda": busqueda,
    }

    return render(request, "reportes/facturas_pagadas.html", contexto)

@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def facturas_anuladas(request):
    busqueda = request.GET.get("q", "")

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
        "actualizado_por",
    ).filter(
        estado="ANULADA",
        activo=True,
    ).order_by("-fecha_anulacion")

    if busqueda:
        facturas = (
            facturas.filter(numero__icontains=busqueda)
            | facturas.filter(abonado__nombres__icontains=busqueda)
            | facturas.filter(abonado__apellidos__icontains=busqueda)
            | facturas.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    return render(request, "reportes/facturas_anuladas.html", {
        "facturas": facturas,
        "busqueda": busqueda,
    })