from django.contrib import admin

from .models import TarifaAgua, RangoTarifaAgua, Rubro


class RangoTarifaAguaInline(admin.TabularInline):
    model = RangoTarifaAgua
    extra = 1


@admin.register(TarifaAgua)
class TarifaAguaAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "valor_base",
        "consumo_base",
        "valor_excedente",
        "vigente",
        "activo",
    )

    search_fields = ("nombre",)

    list_filter = (
        "vigente",
        "activo",
    )

    inlines = [RangoTarifaAguaInline]


@admin.register(Rubro)
class RubroAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "tipo",
        "forma_calculo",
        "valor",
        "aplica_automaticamente",
        "vigente",
        "activo",
    )

    search_fields = ("nombre",)

    list_filter = (
        "tipo",
        "forma_calculo",
        "aplica_automaticamente",
        "vigente",
        "activo",
    )