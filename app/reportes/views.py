from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from pagos.models import Pago
from facturacion.models import Factura
from usuarios.decoradores import rol_requerido
from decimal import Decimal
from django.utils import timezone
from pagos.models import Pago
from django.http import HttpResponse
from openpyxl import Workbook
from datetime import date
from calendar import monthrange
from django.db.models.functions import TruncDate
from django.db.models import Count
from django.db.models import Sum
from django.db.models import Count
from facturacion.models import Factura


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


@login_required
def recaudacion_diaria(request):
    fecha = request.GET.get("fecha") or timezone.localdate()

    pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "creado_por",
    ).prefetch_related(
        "factura__detalles"
    ).filter(
        fecha_pago__date=fecha,
        activo=True,
        anulado=False,
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
            valor = detalle.valor_total * proporcion

            if detalle.tipo == "AGUA":
                total_agua += valor
            elif detalle.tipo == "ALCANTARILLADO":
                total_alcantarillado += valor
            elif detalle.tipo == "MULTA":
                total_multas += valor
            else:
                total_otros += valor

    return render(request, "reportes/recaudacion_diaria.html", {
        "fecha": fecha,
        "pagos": pagos,
        "total_pagos": pagos.count(),
        "total_recaudado": total_recaudado,
        "total_agua": total_agua,
        "total_alcantarillado": total_alcantarillado,
        "total_multas": total_multas,
        "total_otros": total_otros,
    })


@login_required
def exportar_recaudacion_diaria_excel(request):
    fecha = request.GET.get("fecha") or timezone.localdate()

    pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "creado_por",
    ).filter(
        fecha_pago__date=fecha,
        activo=True,
        anulado=False,
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Recaudación diaria"

    ws.append(["RECAUDACIÓN DIARIA"])
    ws.append(["Fecha", str(fecha)])
    ws.append([])

    ws.append([
        "Hora",
        "Factura",
        "Abonado",
        "Método",
        "Cajero",
        "Valor pagado",
    ])

    total = 0

    for pago in pagos:
        total += pago.valor_pagado

        ws.append([
            pago.fecha_pago.strftime("%H:%M"),
            pago.factura.numero,
            str(pago.factura.abonado),
            pago.metodo_pago,
            str(pago.creado_por or "-"),
            float(pago.valor_pagado),
        ])

    ws.append([])
    ws.append(["", "", "", "", "TOTAL", float(total)])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="recaudacion_diaria_{fecha}.xlsx"'
    )

    wb.save(response)
    return response


@login_required
def recaudacion_mensual(request):
    hoy = timezone.localdate()

    anio = int(request.GET.get("anio", hoy.year))
    mes = int(request.GET.get("mes", hoy.month))

    fecha_inicio = date(anio, mes, 1)
    fecha_fin = date(anio, mes, monthrange(anio, mes)[1])

    pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "creado_por",
    ).prefetch_related(
        "factura__detalles"
    ).filter(
        fecha_pago__date__gte=fecha_inicio,
        fecha_pago__date__lte=fecha_fin,
        activo=True,
        anulado=False,
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
            valor = detalle.valor_total * proporcion

            if detalle.tipo == "AGUA":
                total_agua += valor
            elif detalle.tipo == "ALCANTARILLADO":
                total_alcantarillado += valor
            elif detalle.tipo == "MULTA":
                total_multas += valor
            else:
                total_otros += valor

    resumen_diario = pagos.annotate(
        dia=TruncDate("fecha_pago")
    ).values("dia").annotate(
        total=Sum("valor_pagado"),
        cantidad=Count("id")
    ).order_by("dia")

    return render(request, "reportes/recaudacion_mensual.html", {
        "anio": anio,
        "mes": mes,
        "pagos": pagos,
        "resumen_diario": resumen_diario,
        "total_pagos": pagos.count(),
        "total_recaudado": total_recaudado,
        "total_agua": total_agua,
        "total_alcantarillado": total_alcantarillado,
        "total_multas": total_multas,
        "total_otros": total_otros,
    })


@login_required
def exportar_recaudacion_mensual_excel(request):
    hoy = timezone.localdate()

    anio = int(request.GET.get("anio", hoy.year))
    mes = int(request.GET.get("mes", hoy.month))

    fecha_inicio = date(anio, mes, 1)
    fecha_fin = date(anio, mes, monthrange(anio, mes)[1])

    pagos = Pago.objects.select_related(
        "factura",
        "factura__abonado",
        "creado_por",
    ).filter(
        fecha_pago__date__gte=fecha_inicio,
        fecha_pago__date__lte=fecha_fin,
        activo=True,
        anulado=False,
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Recaudación mensual"

    ws.append(["RECAUDACIÓN MENSUAL"])
    ws.append(["Año", anio])
    ws.append(["Mes", mes])
    ws.append([])

    ws.append([
        "Fecha",
        "Factura",
        "Abonado",
        "Método",
        "Cajero",
        "Valor pagado",
    ])

    total = 0

    for pago in pagos:
        total += pago.valor_pagado

        ws.append([
            pago.fecha_pago.strftime("%Y-%m-%d %H:%M"),
            pago.factura.numero,
            str(pago.factura.abonado),
            pago.metodo_pago,
            str(pago.creado_por or "-"),
            float(pago.valor_pagado),
        ])

    ws.append([])
    ws.append(["", "", "", "", "TOTAL", float(total)])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="recaudacion_mensual_{anio}_{mes}.xlsx"'
    )

    wb.save(response)
    return response

@login_required
def cartera_vencida(request):

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
    ).filter(
        activo=True,
        estado__in=["PENDIENTE", "PARCIAL"]
    ).order_by(
        "abonado__apellidos",
        "abonado__nombres",
        "periodo__anio",
        "periodo__mes",
    )

    resumen = {}

    for factura in facturas:
        abonado_id = factura.abonado.id

        if abonado_id not in resumen:
            resumen[abonado_id] = {
                "abonado": factura.abonado,
                "cantidad_facturas": 0,
                "total_deuda": Decimal("0.00"),
                "facturas": [],
            }

        resumen[abonado_id]["cantidad_facturas"] += 1
        resumen[abonado_id]["total_deuda"] += factura.saldo_pendiente
        resumen[abonado_id]["facturas"].append(factura)

    cartera = list(resumen.values())

    cartera.sort(
        key=lambda x: x["total_deuda"],
        reverse=True
    )

    total_deuda_general = sum(
        item["total_deuda"] for item in cartera
    )

    return render(request, "reportes/cartera_vencida.html", {
        "cartera": cartera,
        "total_deuda_general": total_deuda_general,
        "total_abonados_mora": len(cartera),
    })

@login_required
def exportar_cartera_vencida_excel(request):

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
    ).filter(
        activo=True,
        estado__in=["PENDIENTE", "PARCIAL"]
    ).order_by(
        "abonado__apellidos",
        "abonado__nombres",
    )

    resumen = {}

    for factura in facturas:
        abonado_id = factura.abonado.id

        if abonado_id not in resumen:
            resumen[abonado_id] = {
                "abonado": factura.abonado,
                "cantidad_facturas": 0,
                "total_deuda": Decimal("0.00"),
                "periodos": [],
            }

        resumen[abonado_id]["cantidad_facturas"] += 1
        resumen[abonado_id]["total_deuda"] += factura.saldo_pendiente

        resumen[abonado_id]["periodos"].append(
            f"{factura.periodo.nombre} (${factura.saldo_pendiente})"
        )

    cartera = list(resumen.values())

    wb = Workbook()
    ws = wb.active
    ws.title = "Cartera vencida"

    ws.append(["CARTERA VENCIDA"])
    ws.append([])

    ws.append([
        "Abonado",
        "Cédula/RUC",
        "Facturas pendientes",
        "Total deuda",
        "Períodos pendientes",
    ])

    total_general = Decimal("0.00")

    for item in cartera:
        total_general += item["total_deuda"]

        ws.append([
            str(item["abonado"]),
            item["abonado"].cedula_ruc,
            item["cantidad_facturas"],
            float(item["total_deuda"]),
            ", ".join(item["periodos"]),
        ])

    ws.append([])
    ws.append(["", "", "", float(total_general)])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = (
        'attachment; filename="cartera_vencida.xlsx"'
    )

    wb.save(response)

    return response

