from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Abonado


@login_required
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

    contexto = {
        "abonados": abonados,
        "busqueda": busqueda,
    }

    return render(request, "abonados/lista.html", contexto)