from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from abonados.models import Abonado
from facturacion.models import Factura
from pagos.models import Pago
from lecturas.models import Lectura
from auditoria.models import Auditoria


@login_required
def inicio(request):
    hoy = timezone.localdate()

    pagos_hoy = Pago.objects.select_related("factura").prefetch_related(
        "factura__detalles"
    ).filter(
        fecha_pago__date=hoy,
        activo=True,
        anulado=False,
    )

    recaudado_hoy = Decimal("0.00")
    agua_hoy = Decimal("0.00")
    alcantarillado_hoy = Decimal("0.00")
    multas_hoy = Decimal("0.00")

    for pago in pagos_hoy:
        recaudado_hoy += pago.valor_pagado

        factura = pago.factura
        if factura.total <= 0:
            continue

        proporcion = pago.valor_pagado / factura.total

        for detalle in factura.detalles.all():
            valor = detalle.valor_total * proporcion

            if detalle.tipo == "AGUA":
                agua_hoy += valor
            elif detalle.tipo == "ALCANTARILLADO":
                alcantarillado_hoy += valor
            elif detalle.tipo == "MULTA":
                multas_hoy += valor

    total_abonados = Abonado.objects.filter(activo=True).count()

    facturas_pendientes = Factura.objects.filter(
        estado__in=["PENDIENTE", "PARCIAL"],
        activo=True,
    ).count()

    cartera_pendiente = Factura.objects.filter(
        estado__in=["PENDIENTE", "PARCIAL"],
        activo=True,
    ).aggregate(total=Sum("saldo_pendiente"))["total"] or 0

    lecturas_pendientes = Lectura.objects.filter(
        activo=True,
        factura__isnull=True,
        lectura_actual=models.F("lectura_anterior"),
    ).count()

    pagos_registrados_hoy = pagos_hoy.count()

    ultimas_acciones = Auditoria.objects.select_related("usuario").all()[:8]

    contexto = {
        "recaudado_hoy": recaudado_hoy,
        "agua_hoy": agua_hoy,
        "alcantarillado_hoy": alcantarillado_hoy,
        "multas_hoy": multas_hoy,
        "pagos_registrados_hoy": pagos_registrados_hoy,
        "total_abonados": total_abonados,
        "facturas_pendientes": facturas_pendientes,
        "cartera_pendiente": cartera_pendiente,
        "lecturas_pendientes": lecturas_pendientes,
        "ultimas_acciones": ultimas_acciones,
    }

    return render(request, "panel/inicio.html", contexto)