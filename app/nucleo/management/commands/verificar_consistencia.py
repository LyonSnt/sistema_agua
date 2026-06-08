from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.models import DecimalField, F, Q, Sum, Value
from django.db.models.functions import Coalesce

from facturacion.models import Factura
from lecturas.models import Lectura
from pagos.models import Pago
from tenants.database import configurar_base_tenant
from tenants.models import Tenant


DECIMAL_FIELD = DecimalField(max_digits=10, decimal_places=2)


class Command(BaseCommand):
    help = "Verifica inconsistencias operativas en facturas, pagos y lecturas."

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Alias de base a verificar. Por defecto: default.",
        )
        parser.add_argument(
            "--tenant",
            help="Slug de tenant a verificar. Tiene prioridad sobre --database.",
        )
        parser.add_argument(
            "--all-tenants",
            action="store_true",
            help="Verifica todos los tenants activos registrados en master.",
        )
        parser.add_argument(
            "--fail-on-issues",
            action="store_true",
            help="Termina con error si encuentra inconsistencias.",
        )

    def handle(self, *args, **options):
        objetivos = self._resolver_objetivos(options)
        total_inconsistencias = 0

        for etiqueta, alias in objetivos:
            total_inconsistencias += self._verificar_base(etiqueta, alias)

        if total_inconsistencias:
            mensaje = (
                f"Inconsistencias encontradas: {total_inconsistencias}."
            )
            if options["fail_on_issues"]:
                raise CommandError(mensaje)

            self.stdout.write(self.style.WARNING(mensaje))
            return

        self.stdout.write(
            self.style.SUCCESS("No se encontraron inconsistencias operativas.")
        )

    def _resolver_objetivos(self, options):
        if options["all_tenants"] and options["tenant"]:
            raise CommandError("Use --tenant o --all-tenants, no ambos.")

        if options["all_tenants"]:
            tenants = Tenant.objects.using("master").filter(
                activo=True
            ).order_by("slug")
            objetivos = []

            for tenant in tenants:
                objetivos.append(
                    (tenant.slug, configurar_base_tenant(tenant))
                )

            if not objetivos:
                raise CommandError("No existen tenants activos para verificar.")

            return objetivos

        if options["tenant"]:
            slug = options["tenant"].strip().lower()

            try:
                tenant = Tenant.objects.using("master").get(slug=slug)
            except Tenant.DoesNotExist as exc:
                raise CommandError(
                    f"No existe un tenant con slug '{slug}'."
                ) from exc

            if not tenant.activo:
                raise CommandError(f"El tenant '{slug}' esta inactivo.")

            return [(tenant.slug, configurar_base_tenant(tenant))]

        alias = options["database"]

        if alias not in connections.databases:
            raise CommandError(f"No existe el alias de base '{alias}'.")

        return [(alias, alias)]

    def _verificar_base(self, etiqueta, alias):
        self.stdout.write(f"Verificando {etiqueta} ({alias})...")

        total = 0
        total += self._facturas_con_saldos_descuadrados(alias)
        total += self._pagos_activos_en_facturas_anuladas(alias)
        total += self._facturas_pagadas_con_saldo(alias)
        total += self._facturas_con_pago_excedido(alias)
        total += self._lecturas_registradas_sin_factura(alias)

        if total == 0:
            self.stdout.write(
                self.style.SUCCESS(f"{etiqueta}: sin inconsistencias.")
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    f"{etiqueta}: {total} inconsistencias detectadas."
                )
            )

        return total

    def _facturas_con_saldos_descuadrados(self, alias):
        facturas = self._facturas_con_total_pagado_calculado(alias).exclude(
            estado="ANULADA"
        )

        inconsistentes = []

        for factura in facturas.iterator():
            total_pagado_calculado = factura.total_pagado_calculado
            saldo_calculado = factura.total - total_pagado_calculado

            if (
                factura.total_pagado != total_pagado_calculado
                or factura.saldo_pendiente != saldo_calculado
            ):
                inconsistentes.append(
                    (
                        factura.numero,
                        factura.total_pagado,
                        total_pagado_calculado,
                        factura.saldo_pendiente,
                        saldo_calculado,
                    )
                )

        if not inconsistentes:
            return 0

        self.stdout.write("  Facturas con saldo o total pagado descuadrado:")
        for numero, total, total_calc, saldo, saldo_calc in inconsistentes:
            self.stdout.write(
                "  - "
                f"{numero}: total_pagado={total} esperado={total_calc}; "
                f"saldo={saldo} esperado={saldo_calc}"
            )

        return len(inconsistentes)

    def _pagos_activos_en_facturas_anuladas(self, alias):
        pagos = Pago.objects.using(alias).filter(
            activo=True,
            anulado=False,
            factura__estado="ANULADA",
        ).select_related("factura")

        cantidad = pagos.count()

        if cantidad:
            self.stdout.write("  Pagos activos sobre facturas anuladas:")
            for pago in pagos.iterator():
                self.stdout.write(
                    f"  - pago={pago.id} factura={pago.factura.numero}"
                )

        return cantidad

    def _facturas_pagadas_con_saldo(self, alias):
        facturas = Factura.objects.using(alias).filter(
            activo=True,
            estado="PAGADA",
        ).exclude(saldo_pendiente=Decimal("0.00"))

        cantidad = facturas.count()

        if cantidad:
            self.stdout.write("  Facturas pagadas con saldo pendiente:")
            for factura in facturas.iterator():
                self.stdout.write(
                    f"  - {factura.numero}: saldo={factura.saldo_pendiente}"
                )

        return cantidad

    def _facturas_con_pago_excedido(self, alias):
        facturas = self._facturas_con_total_pagado_calculado(alias).filter(
            total_pagado_calculado__gt=F("total")
        )

        cantidad = facturas.count()

        if cantidad:
            self.stdout.write("  Facturas con pagos mayores al total:")
            for factura in facturas.iterator():
                self.stdout.write(
                    "  - "
                    f"{factura.numero}: total={factura.total} "
                    f"pagado={factura.total_pagado_calculado}"
                )

        return cantidad

    def _lecturas_registradas_sin_factura(self, alias):
        lecturas = Lectura.objects.using(alias).filter(
            activo=True,
            lectura_registrada=True,
            factura__isnull=True,
        ).select_related("periodo", "medidor", "medidor__abonado")

        cantidad = lecturas.count()

        if cantidad:
            self.stdout.write("  Lecturas registradas sin factura:")
            for lectura in lecturas.iterator():
                self.stdout.write(
                    "  - "
                    f"lectura={lectura.id} periodo={lectura.periodo} "
                    f"abonado={lectura.medidor.abonado}"
                )

        return cantidad

    def _facturas_con_total_pagado_calculado(self, alias):
        return Factura.objects.using(alias).filter(
            activo=True,
        ).annotate(
            total_pagado_calculado=Coalesce(
                Sum(
                    "pagos__valor_pagado",
                    filter=Q(
                        pagos__activo=True,
                        pagos__anulado=False,
                    ),
                ),
                Value(Decimal("0.00"), output_field=DECIMAL_FIELD),
                output_field=DECIMAL_FIELD,
            )
        )
