from django.shortcuts import get_object_or_404, redirect, render
from facturacion.models import Factura, FacturaDetalle

from django.contrib import messages
from lecturas.models import PeriodoFacturacion, Lectura
from facturacion.servicios import generar_factura_desde_lectura
from django.utils import timezone
from usuarios.decoradores import rol_requerido
from auditoria.utils import registrar_auditoria

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from configuracion_institucional.utils import obtener_configuracion
from tarifas.models import Rubro
from decimal import Decimal
from django.db.models import Sum
from django.core.paginator import Paginator
from django.views.decorators.http import require_http_methods


@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def facturas_pendientes(request):
    busqueda = request.GET.get("q", "")

    facturas = Factura.objects.select_related(
        "abonado",
        "periodo",
    ).filter(
        estado="PENDIENTE",
        activo=True,
    )

    if busqueda:
        facturas = (
            facturas.filter(numero__icontains=busqueda)
            | facturas.filter(abonado__nombres__icontains=busqueda)
            | facturas.filter(abonado__apellidos__icontains=busqueda)
            | facturas.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    paginator = Paginator(facturas, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "facturacion/pendientes.html", {
        "facturas": page_obj,
        "page_obj": page_obj,
        "busqueda": busqueda,
        "querystring": f"q={busqueda}",
    })

#@rol_requerido("Administrador", "Supervisor", "Cajero")
@rol_requerido(
    "Administrador",
    "Supervisor",
    "Cajero",
    "Consulta"
)
def detalle_factura(request, factura_id):
    factura = get_object_or_404(
        Factura.objects.select_related(
            "abonado",
            "periodo",
            "lectura",
            "lectura__medidor",
        ).prefetch_related("detalles", "pagos"),
        id=factura_id,
        activo=True,
    )

    return render(request, "facturacion/detalle.html", {
        "factura": factura,
    })

@rol_requerido("Administrador", "Supervisor")
@require_http_methods(["GET", "POST"])
def generar_facturacion_periodo(request):
    periodos = PeriodoFacturacion.objects.filter(activo=True).order_by("-anio", "-mes")

    if request.method == "POST":
        periodo_id = request.POST.get("periodo")
        periodo = get_object_or_404(PeriodoFacturacion, id=periodo_id, activo=True)

        lecturas = Lectura.objects.filter(
            periodo=periodo,
            activo=True,
        ).select_related("medidor", "medidor__abonado")

        generadas = 0
        existentes = 0
        errores = 0
        pendientes = 0

        for lectura in lecturas:
            try:
                # Ya facturada
                if hasattr(lectura, "factura"):
                    existentes += 1
                    continue

                # Lectura pendiente
                if not lectura.lectura_registrada:
                    pendientes += 1
                    continue

                # Generar factura
                factura = generar_factura_desde_lectura(
                    lectura,
                    request.user
                )

                registrar_auditoria(
                    request,
                    accion="GENERAR_FACTURA",
                    modulo="Facturación",
                    descripcion=(
                        f"Generó la factura {factura.numero} "
                        f"del abonado {factura.abonado}"
                    ),
                    objeto=factura,
                )

                generadas += 1

            except Exception as e:
                errores += 1
                print(
                    f"Error generando factura para lectura "
                    f"{lectura.id}: {e}"
                )

        messages.success(
            request,
            (
                f"Proceso finalizado para {periodo.nombre}. "
                f"Facturas generadas: {generadas}. "
                f"Ya existentes: {existentes}. "
                f"Lecturas pendientes: {pendientes}. "
                f"Errores técnicos: {errores}."
            )
        )

        return redirect("facturacion:generar")
    
    periodo_consulta_id = request.GET.get("periodo")
    resumen = None

    if periodo_consulta_id:
        periodo_consulta = get_object_or_404(
            PeriodoFacturacion,
            id=periodo_consulta_id,
            activo=True,
        )

        lecturas_consulta = Lectura.objects.filter(
            periodo=periodo_consulta,
            activo=True,
        )

        total_lecturas = lecturas_consulta.count()
        pendientes = 0
        listas = 0
        facturadas = 0

        for lectura in lecturas_consulta:
            if hasattr(lectura, "factura"):
                facturadas += 1
            elif lectura.lectura_actual == lectura.lectura_anterior:
                pendientes += 1
            else:
                listas += 1

        resumen = {
            "periodo": periodo_consulta,
            "total_lecturas": total_lecturas,
            "pendientes": pendientes,
            "listas": listas,
            "facturadas": facturadas,
        }

    return render(request, "facturacion/generar.html", {
        "periodos": periodos,
        "resumen": resumen,
        "periodo_consulta_id": periodo_consulta_id,
    })

@rol_requerido("Administrador")
@require_http_methods(["GET", "POST"])
def anular_factura(request, factura_id):
    factura = get_object_or_404(
        Factura,
        id=factura_id,
        activo=True,
    )

    pagos_activos = factura.pagos.filter(
        activo=True,
        anulado=False
    ).exists()

    if pagos_activos:
        messages.error(
            request,
            "No se puede anular la factura porque tiene pagos activos. Primero debe anular los pagos."
        )
        return redirect("facturacion:detalle", factura_id=factura.id)

    if factura.estado == "ANULADA":
        messages.error(request, "La factura ya se encuentra anulada.")
        return redirect("facturacion:detalle", factura_id=factura.id)

    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()

        if not motivo:
            messages.error(request, "Debe ingresar el motivo de anulación.")
            return redirect("facturacion:anular", factura_id=factura.id)

        factura.estado = "ANULADA"
        factura.fecha_anulacion = timezone.now()
        factura.motivo_anulacion = motivo
        factura.actualizado_por = request.user
        factura.save()

        registrar_auditoria(
            request,
            accion="ANULAR_FACTURA",
            modulo="Facturación",
            descripcion=(
                f"Anuló la factura {factura.numero} "
                f"del abonado {factura.abonado}. Motivo: {motivo}"
            ),
            objeto=factura,
        )

        messages.success(request, "Factura anulada correctamente.")
        return redirect("facturacion:detalle", factura_id=factura.id)

    return render(request, "facturacion/anular.html", {
        "factura": factura,
    })

@rol_requerido("Administrador", "Supervisor", "Cajero", "Consulta")
def factura_pdf(request, factura_id):
    factura = get_object_or_404(
        Factura.objects.select_related(
            "abonado",
            "periodo",
            "lectura",
            "lectura__medidor",
        ).prefetch_related("detalles", "pagos"),
        id=factura_id,
        activo=True,
    )

    html_string = render_to_string(
        "facturacion/pdf_factura.html",
       {
            "factura": factura,
            "configuracion": obtener_configuracion(),
        }
    )

    pdf = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="factura_{factura.numero}.pdf"'
    )

    return response


@rol_requerido("Administrador", "Supervisor")
@require_http_methods(["GET", "POST"])
def agregar_rubro_factura(request, factura_id):

    factura = get_object_or_404(
        Factura.objects.prefetch_related("detalles"),
        id=factura_id,
        activo=True
    )

    if factura.estado != "PENDIENTE":
        messages.error(
            request,
            "Solo se pueden agregar rubros a facturas pendientes."
        )

        return redirect(
            "facturacion:detalle",
            factura_id=factura.id
        )

    rubros = Rubro.objects.filter(
        activo=True,
        vigente=True,
        aplica_automaticamente=False
    ).order_by("nombre")

    if request.method == "POST":

        rubro_id = request.POST.get("rubro")

        rubro = get_object_or_404(
            Rubro,
            id=rubro_id,
            activo=True
        )

        valor = Decimal(rubro.valor)

        ya_existe = factura.detalles.filter(
            descripcion=rubro.nombre,
            tipo=rubro.tipo,
        ).exists()

        if ya_existe:
            messages.error(
                request,
                (
                    f"El rubro '{rubro.nombre}' ya se encuentra "
                    f"registrado en la factura {factura.numero}. "
                    f"No es posible agregarlo nuevamente."
                )
            )
            return redirect("facturacion:agregar_rubro", factura_id=factura.id)

        FacturaDetalle.objects.create(
            factura=factura,
            descripcion=rubro.nombre,
            cantidad=1,
            valor_unitario=valor,
            tipo=rubro.tipo,
            creado_por=request.user,
            actualizado_por=request.user,
        )

        total = factura.detalles.aggregate(
            total=Sum("valor_total")
        )["total"] or 0

        factura.subtotal = total
        factura.total = total
        factura.saldo_pendiente = total

        factura.save()

        registrar_auditoria(
            request,
            accion="AGREGAR_RUBRO",
            modulo="Facturación",
            descripcion=(
                f"Agregó rubro manual "
                f"{rubro.nombre} "
                f"a factura {factura.numero}"
            ),
            objeto=factura,
        )

        messages.success(
            request,
            "Rubro agregado correctamente."
        )

        return redirect(
            "facturacion:detalle",
            factura_id=factura.id
        )

    return render(
        request,
        "facturacion/agregar_rubro.html",
        {
            "factura": factura,
            "rubros": rubros,
        }
    )
