from decimal import Decimal
from datetime import timedelta

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
from medidores.models import CambioMedidor
from multas.models import Multa
from usuarios.decoradores import rol_requerido


@rol_requerido(
    "Administrador",
    "Supervisor",
    "Cajero",
    "Lecturista",
    "Consulta"
)
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

    abonados_suspendidos = Abonado.objects.filter(
        activo=True,
        estado_servicio="SUSPENDIDO",
    )

    pendientes_reconexion = [
        abonado
        for abonado in abonados_suspendidos.select_related("sector", "ruta")
        if abonado.estado_cuenta() == "AL_DIA"
    ]

    multas_pendientes_qs = Multa.objects.select_related(
        "abonado"
    ).filter(
        activo=True,
        estado="PENDIENTE",
    ).order_by("-fecha", "-id")

    pagos_anulados_recientes = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "actualizado_por",
    ).filter(
        activo=True,
        anulado=True,
        fecha_anulacion__date__gte=hace_7_dias,
    ).order_by("-fecha_anulacion")[:5]

    facturas_anuladas_recientes = Factura.objects.select_related(
        "abonado",
        "periodo",
        "actualizado_por",
    ).filter(
        activo=True,
        estado="ANULADA",
        fecha_anulacion__date__gte=hace_7_dias,
    ).order_by("-fecha_anulacion")[:5]

    cambios_medidor_recientes = CambioMedidor.objects.select_related(
        "abonado",
        "medidor_anterior",
        "medidor_nuevo",
        "creado_por",
    ).filter(
        activo=True,
        fecha_cambio__gte=hace_7_dias,
    ).order_by("-fecha_cambio", "-id")[:5]

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
        "abonados_suspendidos": abonados_suspendidos.count(),
        "pendientes_reconexion": pendientes_reconexion[:5],
        "pendientes_reconexion_total": len(pendientes_reconexion),
        "multas_pendientes": multas_pendientes_qs[:5],
        "multas_pendientes_total": multas_pendientes_qs.count(),
        "pagos_anulados_recientes": pagos_anulados_recientes,
        "facturas_anuladas_recientes": facturas_anuladas_recientes,
        "cambios_medidor_recientes": cambios_medidor_recientes,

        "ultimos_pagos": ultimos_pagos,
        "ultimas_acciones": ultimas_acciones,
    }

    return render(request, "panel/inicio.html", contexto)
