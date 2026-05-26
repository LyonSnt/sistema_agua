from decimal import Decimal

from django.db import transaction

from tarifas.models import TarifaAgua, Rubro
from .models import Factura, FacturaDetalle


def generar_numero_factura():
    ultima = Factura.objects.order_by("-id").first()

    if not ultima:
        return "FAC-000001"

    ultimo_numero = int(ultima.numero.replace("FAC-", ""))
    nuevo_numero = ultimo_numero + 1

    return f"FAC-{nuevo_numero:06d}"


def calcular_valor_agua(consumo, tarifa):
    consumo = Decimal(consumo)
    valor = Decimal(tarifa.valor_base)
    consumo_base = Decimal(tarifa.consumo_base)

    if consumo <= consumo_base:
        return valor

    rangos = tarifa.rangos.filter(activo=True).order_by("desde")

    if not rangos.exists():
        excedente = consumo - consumo_base
        return valor + (excedente * Decimal(tarifa.valor_excedente))

    for rango in rangos:
        desde = Decimal(rango.desde)
        hasta = Decimal(rango.hasta) if rango.hasta is not None else consumo

        if consumo > desde:
            limite_superior = min(consumo, hasta)
            unidades = limite_superior - desde

            if unidades > 0:
                valor += unidades * Decimal(rango.valor_por_unidad)

    return valor

def calcular_excedente(consumo, tarifa):
    consumo = Decimal(consumo)
    consumo_base = Decimal(tarifa.consumo_base)

    if consumo <= consumo_base:
        return Decimal("0.00")

    excedente = Decimal("0.00")

    rangos = tarifa.rangos.filter(
        activo=True
    ).order_by("desde")

    if not rangos.exists():
        unidades = consumo - consumo_base
        return unidades * Decimal(tarifa.valor_excedente)

    for rango in rangos:
        desde = Decimal(rango.desde)
        hasta = Decimal(rango.hasta) if rango.hasta else consumo

        if consumo > desde:
            limite_superior = min(consumo, hasta)

            unidades = limite_superior - desde

            if unidades > 0:
                excedente += (
                    unidades *
                    Decimal(rango.valor_por_unidad)
                )

    return excedente

@transaction.atomic
def generar_factura_desde_lectura(lectura, usuario=None):
    if hasattr(lectura, "factura"):
        return lectura.factura
    
    if not lectura.lectura_registrada:
        raise ValueError(
            "No se puede generar factura porque la lectura aún no ha sido registrada."
        )

    tarifa = TarifaAgua.objects.filter(
        vigente=True,
        activo=True
    ).first()

    if not tarifa:
        raise ValueError("No existe una tarifa de agua vigente.")

    abonado = lectura.medidor.abonado
    consumo = lectura.consumo

    factura = Factura.objects.create(
        numero=generar_numero_factura(),
        abonado=abonado,
        periodo=lectura.periodo,
        lectura=lectura,
        creado_por=usuario,
        actualizado_por=usuario,
    )

    # Valor de agua
    valor_agua = calcular_valor_agua(consumo, tarifa)
    valor_base = Decimal(tarifa.valor_base)

    valor_excedente = calcular_excedente(
        consumo,
        tarifa
    )

    # FacturaDetalle.objects.create(
    #     factura=factura,
    #     descripcion=f"Consumo de agua potable ({consumo} m³)",
    #     cantidad=1,
    #     valor_unitario=valor_agua,
    #     tipo="AGUA",
    #     creado_por=usuario,
    #     actualizado_por=usuario,
    # )

    FacturaDetalle.objects.create(
        factura=factura,
        descripcion=(
            f"Cargo básico agua potable "
            f"({tarifa.consumo_base} m³ incluidos)"
        ),
        cantidad=1,
        valor_unitario=valor_base,
        tipo="AGUA",
        creado_por=usuario,
        actualizado_por=usuario,
    )

    # if valor_excedente > 0:
    #     excedente_m3 = (
    #         Decimal(consumo) -
    #         Decimal(tarifa.consumo_base)
    #     )

    excedente_m3 = max(
        Decimal(consumo) -
        Decimal(tarifa.consumo_base),
        Decimal("0.00")
    )

    FacturaDetalle.objects.create(
        factura=factura,
        descripcion=(
            f"Excedente consumo "
            f"({excedente_m3} m³ × "
            f"${tarifa.valor_excedente})"
        ),
        cantidad=1,
        valor_unitario=valor_excedente,
        tipo="AGUA",
        creado_por=usuario,
        actualizado_por=usuario,
    )

    # Rubros automáticos: alcantarillado, multas u otros
    rubros = Rubro.objects.filter(
        aplica_automaticamente=True,
        vigente=True,
        activo=True
    )

    for rubro in rubros:
        valor = rubro.valor

        if rubro.forma_calculo == "PORCENTAJE":
            valor = valor_agua * (rubro.valor / Decimal("100"))

        FacturaDetalle.objects.create(
            factura=factura,
            descripcion=rubro.nombre,
            cantidad=1,
            valor_unitario=valor,
            tipo=rubro.tipo,
            creado_por=usuario,
            actualizado_por=usuario,
        )

    factura.calcular_totales()

    return factura