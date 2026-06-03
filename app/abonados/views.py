from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Abonado
from django.core.paginator import Paginator
from usuarios.decoradores import rol_requerido

from django.shortcuts import render, get_object_or_404
from .models import Abonado
from pagos.models import Pago
from medidores.models import Medidor
from lecturas.models import Lectura


@rol_requerido(
    "Administrador",
    "Supervisor",
    "Cajero",
    "Lecturista",
    "Consulta"
)
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

@rol_requerido(
    "Administrador",
    "Supervisor",
    "Cajero",
    "Lecturista",
    "Consulta"
)
def detalle_abonado(request, abonado_id):
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

    medidor = abonado.medidores.filter(
        activo=True
    ).first()

    ultima_lectura = None

    if medidor:
        ultima_lectura = medidor.lecturas.order_by(
            "-periodo__anio",
            "-periodo__mes"
        ).first()



    contexto = {
        "abonado": abonado,
        "facturas": facturas,
        "pagos": pagos,
        "medidor": medidor,
        "ultima_lectura": ultima_lectura,
        "total_facturado": total_facturado,
        "total_pagado": total_pagado,
        "saldo_pendiente": saldo_pendiente,
        "facturas_pendientes": facturas_pendientes,
        "facturas_pagadas": facturas_pagadas,
        "historial_suspensiones": historial_suspensiones,
    }

    return render(
        request,
        "abonados/detalle_abonado.html",
        contexto
    )









