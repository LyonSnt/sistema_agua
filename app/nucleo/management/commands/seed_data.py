import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from faker import Faker

from abonados.models import Sector, Ruta, Abonado
from medidores.models import Medidor
from lecturas.models import PeriodoFacturacion, Lectura
from tarifas.models import TarifaAgua, Rubro
from facturacion.servicios import generar_factura_desde_lectura
from pagos.models import Pago


class Command(BaseCommand):
    help = "Genera datos de prueba para el sistema"

    def handle(self, *args, **kwargs):
        fake = Faker("es_ES")

        self.stdout.write(self.style.SUCCESS("Generando datos..."))

        # =========================================================
        # SECTORES
        # =========================================================

        sectores = []

        nombres_sectores = [
            "Centro",
            "5 de Marzo",
            "San Pedro",
            "Norte",
            "Sur",
        ]

        for nombre in nombres_sectores:
            sector, _ = Sector.objects.get_or_create(
                nombre=nombre
            )
            sectores.append(sector)

        # =========================================================
        # RUTAS
        # =========================================================

        rutas = []

        for sector in sectores:
            for i in range(1, 4):
                ruta, _ = Ruta.objects.get_or_create(
                    sector=sector,
                    nombre=f"Ruta {i}"
                )
                rutas.append(ruta)

        # =========================================================
        # TARIFA
        # =========================================================

        tarifa, _ = TarifaAgua.objects.get_or_create(
            nombre="Tarifa Básica",
            defaults={
                "valor_base": Decimal("4.00"),
                "consumo_base": Decimal("10"),
                "valor_excedente": Decimal("0.25"),
                "vigente": True,
            }
        )

        # =========================================================
        # RUBRO ALCANTARILLADO
        # =========================================================

        Rubro.objects.get_or_create(
            nombre="Alcantarillado",
            defaults={
                "tipo": "ALCANTARILLADO",
                "forma_calculo": "FIJO",
                "valor": Decimal("1.00"),
                "aplica_automaticamente": True,
                "vigente": True,
            }
        )

        # =========================================================
        # PERIODO
        # =========================================================

        periodo, creado = PeriodoFacturacion.objects.update_or_create(
            anio=2026,
            mes=5,
            defaults={
                "nombre": "Mayo 2026",
                "fecha_inicio": "2026-05-01",
                "fecha_fin": "2026-05-31",
                "estado": "ABIERTO",
                "activo": True,
            }
        )

        # =========================================================
        # ABONADOS + MEDIDORES + LECTURAS
        # =========================================================

        for i in range(1, 51):
            ruta = random.choice(rutas)

            abonado, _ = Abonado.objects.get_or_create(
                codigo=f"AB{i:04}",
                defaults={
                    "cedula_ruc": fake.unique.numerify("##########"),
                    "nombres": fake.first_name(),
                    "apellidos": fake.last_name(),
                    "telefono": fake.numerify("09########"),
                    "correo": fake.email(),
                    "direccion": fake.address(),
                    "referencia": fake.street_name(),
                    "sector": ruta.sector,
                    "ruta": ruta,
                }
            )

            medidor, _ = Medidor.objects.get_or_create(
                numero=f"MED{i:05}",
                defaults={
                    "abonado": abonado,
                    "marca": random.choice(["Genérico", "FlowTech", "Aqua"]),
                    "modelo": random.choice(["A1", "B2", "C3"]),
                    "lectura_inicial": Decimal("0"),
                    "estado": "ACTIVO",
                }
            )

            lectura_actual = Decimal(random.randint(8, 30))

            lectura, creada = Lectura.objects.get_or_create(
                periodo=periodo,
                medidor=medidor,
                defaults={
                    "lectura_anterior": Decimal("0"),
                    "lectura_actual": lectura_actual,
                    "lectura_registrada": True,
                    "observacion": "",
                }
            )

            if creada:
                factura = generar_factura_desde_lectura(lectura)

                # Algunas facturas pagadas aleatoriamente
                if random.choice([True, False]):

                    Pago.objects.get_or_create(
                        factura=factura,
                        defaults={
                            "metodo_pago": "EFECTIVO",
                            "valor_pagado": factura.total,
                        }
                    )

        self.stdout.write(
            self.style.SUCCESS("Datos generados correctamente.")
        )