from decimal import Decimal

from medidores.models import Medidor
from .models import Lectura


def obtener_ultima_lectura(medidor):
    ultima = Lectura.objects.filter(
        medidor=medidor,
        activo=True
    ).order_by("-periodo__anio", "-periodo__mes").first()

    if ultima:
        return ultima.lectura_actual

    return medidor.lectura_inicial or Decimal("0.00")


def generar_lecturas_periodo(periodo):
    medidores = Medidor.objects.filter(
        activo=True,
        estado="ACTIVO"
    ).select_related("abonado")

    creadas = 0
    existentes = 0
    errores = 0

    for medidor in medidores:
        try:
            lectura_anterior = obtener_ultima_lectura(medidor)

            _, creado = Lectura.objects.get_or_create(
                periodo=periodo,
                medidor=medidor,
                defaults={
                    "lectura_anterior": lectura_anterior,
                    "lectura_actual": lectura_anterior,
                    "observacion": "",
                }
            )

            if creado:
                creadas += 1
            else:
                existentes += 1

        except Exception:
            errores += 1

    return {
        "creadas": creadas,
        "existentes": existentes,
        "errores": errores,
    }