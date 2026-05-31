from decimal import Decimal
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from abonados.models import Abonado
from medidores.models import Medidor
from facturacion.models import Factura
from pagos.models import Pago
from lecturas.models import Lectura
from auditoria.models import Auditoria


#@login_required
@login_required(login_url="/login/")
def inicio(request):
    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)
    hace_7_dias = hoy - timedelta(days=6)

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
    total_medidores = Medidor.objects.filter(activo=True).count()

    facturas_pendientes = Factura.objects.filter(
        activo=True,
        estado__in=["PENDIENTE", "PARCIAL"],
    ).count()

    cartera_pendiente = Factura.objects.filter(
        activo=True,
        estado__in=["PENDIENTE", "PARCIAL"],
    ).aggregate(total=Sum("saldo_pendiente"))["total"] or 0

    recaudado_mes = Pago.objects.filter(
        fecha_pago__date__gte=inicio_mes,
        fecha_pago__date__lte=hoy,
        activo=True,
        anulado=False,
    ).aggregate(total=Sum("valor_pagado"))["total"] or 0

    lecturas_pendientes = Lectura.objects.filter(
        activo=True,
        factura__isnull=True,
        lectura_registrada=False,
    ).count()

    abonados_morosos = 0
    for abonado in Abonado.objects.filter(activo=True):
        if abonado.estado_cuenta() == "MOROSO":
            abonados_morosos += 1

    ultimos_pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "creado_por",
    ).filter(
        activo=True,
        anulado=False,
    ).order_by("-fecha_pago")[:8]

    ultimas_acciones = Auditoria.objects.select_related("usuario").all()[:8]

    contexto = {
        "recaudado_hoy": recaudado_hoy,
        "agua_hoy": agua_hoy,
        "alcantarillado_hoy": alcantarillado_hoy,
        "multas_hoy": multas_hoy,
        "pagos_hoy": pagos_hoy.count(),

        "total_abonados": total_abonados,
        "total_medidores": total_medidores,
        "facturas_pendientes": facturas_pendientes,
        "cartera_pendiente": cartera_pendiente,
        "recaudado_mes": recaudado_mes,
        "lecturas_pendientes": lecturas_pendientes,
        "abonados_morosos": abonados_morosos,

        "ultimos_pagos": ultimos_pagos,
        "ultimas_acciones": ultimas_acciones,
    }

    return render(request, "panel/inicio.html", contexto)