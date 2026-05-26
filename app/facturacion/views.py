from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Factura
from django.shortcuts import get_object_or_404

from django.contrib import messages
from django.shortcuts import redirect
from lecturas.models import PeriodoFacturacion, Lectura
from facturacion.servicios import generar_factura_desde_lectura
from django.utils import timezone
from usuarios.decoradores import rol_requerido
from auditoria.utils import registrar_auditoria

from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from configuracion_institucional.utils import obtener_configuracion


@login_required
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

    return render(request, "facturacion/pendientes.html", {
        "facturas": facturas,
        "busqueda": busqueda,
    })


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


@rol_requerido("Administrador", "Supervisor")
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

        messages.success(request, "Factura anulada correctamente.")
        return redirect("facturacion:detalle", factura_id=factura.id)

    return render(request, "facturacion/anular.html", {
        "factura": factura,
    })



@login_required
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