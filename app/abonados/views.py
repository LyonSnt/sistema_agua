from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Abonado
from django.core.paginator import Paginator
from usuarios.decoradores import rol_requerido


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

    return render(request, "abonados/lista.html", contexto)