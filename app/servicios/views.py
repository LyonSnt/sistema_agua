from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from usuarios.decoradores import rol_requerido
from auditoria.utils import registrar_auditoria
from abonados.models import Abonado
from .models import SuspensionServicio
from django.urls import reverse


@rol_requerido("Administrador", "Supervisor")
def lista_suspensiones(request):
    busqueda = request.GET.get("q", "")

    suspensiones = SuspensionServicio.objects.select_related(
        "abonado"
    ).filter(
        activo=True
    ).order_by("-fecha_suspension")

    if busqueda:
        suspensiones = (
            suspensiones.filter(abonado__nombres__icontains=busqueda)
            | suspensiones.filter(abonado__apellidos__icontains=busqueda)
            | suspensiones.filter(abonado__cedula_ruc__icontains=busqueda)
        )

    
    total_suspendidos = SuspensionServicio.objects.filter(
        estado="SUSPENDIDO",
        activo=True
    ).count()

    total_reconectados = SuspensionServicio.objects.filter(
        estado="RECONECTADO",
        activo=True
    ).count()

    total_anulados = SuspensionServicio.objects.filter(
        estado="ANULADO",
        activo=True
    ).count()
    
    return render(request, "servicios/lista.html", {
        "suspensiones": suspensiones,
        "busqueda": busqueda,
        "total_suspendidos": total_suspendidos,
        "total_reconectados": total_reconectados,
        "total_anulados": total_anulados,
    })


@rol_requerido("Administrador", "Supervisor")
def suspender_servicio(request):
    abonado_id = request.GET.get("abonado") or request.POST.get("abonado")

    abonados = Abonado.objects.filter(activo=True)

    if request.method == "POST":
        motivo = request.POST.get("motivo_suspension")

        if not motivo:
            messages.error(request, "Debe ingresar el motivo de suspensión.")
            return redirect("servicios:suspender")

        existe_suspension = SuspensionServicio.objects.filter(
            abonado_id=abonado_id,
            estado="SUSPENDIDO",
            activo=True,
        ).exists()

        if existe_suspension:
            messages.error(
                request,
                "Este abonado ya tiene una suspensión activa."
            )
            # return redirect("servicios:suspender")
            return redirect(f"{reverse('servicios:suspender')}?abonado={abonado_id}")

        suspension = SuspensionServicio.objects.create(
            abonado_id=abonado_id,
            fecha_suspension=request.POST.get("fecha_suspension"),
            motivo_suspension=motivo,
            creado_por=request.user,
            actualizado_por=request.user,
        )

        # Actualizar estado actual del servicio del abonado
        suspension.abonado.estado_servicio = "SUSPENDIDO"
        suspension.abonado.save(update_fields=["estado_servicio"])

        registrar_auditoria(
            request,
            accion="SUSPENDER_SERVICIO",
            modulo="Servicios",
            descripcion=f"Suspendió el servicio de {suspension.abonado}",
            objeto=suspension,
        )

        messages.success(request, "Servicio suspendido correctamente.")
        return redirect("servicios:lista")

    # return render(request, "servicios/suspender.html", {
    #     "abonados": abonados,
    #     "hoy": timezone.localdate(),
    # })
    return render(request, "servicios/suspender.html", {
        "abonados": abonados,
        "abonado_id": abonado_id,
        "hoy": date.today().strftime("%Y-%m-%d")
    })


@rol_requerido("Administrador", "Supervisor")
def reconectar_servicio(request, suspension_id):
    suspension = get_object_or_404(
        SuspensionServicio,
        id=suspension_id,
        activo=True,
        estado="SUSPENDIDO",
    )

    if request.method == "POST":
        suspension.estado = "RECONECTADO"
        suspension.fecha_reconexion = request.POST.get("fecha_reconexion")
        suspension.observacion_reconexion = request.POST.get("observacion_reconexion", "")
        suspension.actualizado_por = request.user
        suspension.save()

        suspension.abonado.estado_servicio = "ACTIVO"
        suspension.abonado.save(update_fields=["estado_servicio"])

        registrar_auditoria(
            request,
            accion="RECONECTAR_SERVICIO",
            modulo="Servicios",
            descripcion=f"Reconectó el servicio de {suspension.abonado}",
            objeto=suspension,
        )

        messages.success(request, "Servicio reconectado correctamente.")
        return redirect("servicios:lista")

    return render(request, "servicios/reconectar.html", {
        "suspension": suspension,
        "hoy": date.today().strftime("%Y-%m-%d")
    })

@rol_requerido("Administrador", "Supervisor")
def reconectar_por_abonado(request, abonado_id):
    suspension = SuspensionServicio.objects.filter(
        abonado_id=abonado_id,
        estado="SUSPENDIDO",
        activo=True,
    ).order_by("-fecha_suspension").first()

    if not suspension:
        messages.error(request, "El abonado no tiene una suspensión activa.")
        return redirect("abonados:lista")

    return redirect("servicios:reconectar", suspension_id=suspension.id)