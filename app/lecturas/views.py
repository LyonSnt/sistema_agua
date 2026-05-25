from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .models import PeriodoFacturacion
from .servicios import generar_lecturas_periodo

from django.db import transaction
from abonados.models import Sector, Ruta
from .models import Lectura
from decimal import Decimal, InvalidOperation
from usuarios.decoradores import rol_requerido


@rol_requerido("Administrador", "Supervisor")
def generar_lecturas(request):
    periodos = PeriodoFacturacion.objects.filter(
        activo=True,
        estado="ABIERTO"
    ).order_by("-anio", "-mes")

    if request.method == "POST":
        periodo_id = request.POST.get("periodo")
        periodo = get_object_or_404(
            PeriodoFacturacion,
            id=periodo_id,
            activo=True,
            estado="ABIERTO",
        )

        resultado = generar_lecturas_periodo(periodo)

        messages.success(
            request,
            f"Proceso finalizado. Lecturas creadas: {resultado['creadas']}. "
            f"Ya existentes: {resultado['existentes']}. "
            f"Errores: {resultado['errores']}."
        )

        return redirect("lecturas:generar")

    return render(request, "lecturas/generar.html", {
        "periodos": periodos,
    })

@rol_requerido("Administrador", "Supervisor", "Lecturista")
def registro_masivo_lecturas(request):
    periodos = PeriodoFacturacion.objects.filter(
        activo=True,
        estado="ABIERTO"
    ).order_by("-anio", "-mes")

    sectores = Sector.objects.filter(activo=True).order_by("nombre")
    rutas = Ruta.objects.filter(activo=True).select_related("sector").order_by("sector__nombre", "nombre")

    periodo_id = request.GET.get("periodo") or request.POST.get("periodo")
    sector_id = request.GET.get("sector") or request.POST.get("sector")
    ruta_id = request.GET.get("ruta") or request.POST.get("ruta")

    periodo_id = request.GET.get("periodo") or request.POST.get("periodo")
    sector_id = request.GET.get("sector") or request.POST.get("sector")
    ruta_id = request.GET.get("ruta") or request.POST.get("ruta")

    if sector_id in ["", "None", None]:
        sector_id = None

    if ruta_id in ["", "None", None]:
        ruta_id = None

    lecturas = Lectura.objects.none()
    periodo_seleccionado = None

    if periodo_id:
        periodo_seleccionado = get_object_or_404(
            PeriodoFacturacion,
            id=periodo_id,
            activo=True,
            estado="ABIERTO",
        )

        lecturas = Lectura.objects.select_related(
            "medidor",
            "medidor__abonado",
            "medidor__abonado__sector",
            "medidor__abonado__ruta",
        ).filter(
            periodo=periodo_seleccionado,
            activo=True,
        ).order_by(
            "medidor__abonado__sector__nombre",
            "medidor__abonado__ruta__nombre",
            "medidor__abonado__apellidos",
            "medidor__abonado__nombres",
        )

        if sector_id:
            lecturas = lecturas.filter(
                medidor__abonado__sector_id=sector_id
            )

        if ruta_id:
            lecturas = lecturas.filter(
                medidor__abonado__ruta_id=ruta_id
            )

    if request.method == "POST" and periodo_seleccionado:
        actualizadas = 0
        errores = 0

        with transaction.atomic():
            for lectura in lecturas:

                if hasattr(lectura, "factura"):
                    continue
                valor = request.POST.get(f"lectura_actual_{lectura.id}")


                if valor is None or valor == "":
                    continue

                try:
                    valor_decimal = Decimal(valor)

                    lectura.lectura_actual = valor_decimal
                    lectura.actualizado_por = request.user
                    lectura.save()
                    actualizadas += 1

                except Exception as e:
                    errores += 1
                    print(f"Error lectura {lectura.id}: {e}")

        messages.success(
            request,
            f"Lecturas actualizadas: {actualizadas}. Errores: {errores}."
        )

        return redirect(
            f"{request.path}?periodo={periodo_id}&sector={sector_id or ''}&ruta={ruta_id or ''}"
        )

    total_lecturas = lecturas.count()
    pendientes_lectura = 0
    listas_facturar = 0
    facturadas = 0

    for lectura in lecturas:
        if hasattr(lectura, "factura"):
            facturadas += 1
        elif lectura.lectura_actual == lectura.lectura_anterior:
            pendientes_lectura += 1
        else:
            listas_facturar += 1

    contexto = {
        "periodos": periodos,
        "sectores": sectores,
        "rutas": rutas,
        "lecturas": lecturas,
        "periodo_id": periodo_id,
        "sector_id": sector_id,
        "ruta_id": ruta_id,
        "contexto_periodo": {
            "total_lecturas": total_lecturas,
            "pendientes_lectura": pendientes_lectura,
            "listas_facturar": listas_facturar,
            "facturadas": facturadas,
        },
    }

    return render(request, "lecturas/registro_masivo.html", contexto)