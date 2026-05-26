from django.urls import path
from . import views

app_name = "reportes"

urlpatterns = [
    path("cierre-diario/", views.cierre_diario, name="cierre_diario"),
    path("cartera/", views.cartera_pendiente, name="cartera"),
    path(
    "facturas-pagadas/",
    views.facturas_pagadas,
    name="facturas_pagadas"
    ),
    path("facturas-anuladas/", views.facturas_anuladas, name="facturas_anuladas"),
    path("recaudacion-diaria/", views.recaudacion_diaria, name="recaudacion_diaria"),
    path(
        "recaudacion-diaria/excel/",
        views.exportar_recaudacion_diaria_excel,
        name="recaudacion_diaria_excel"
    ),
    path("recaudacion-mensual/", views.recaudacion_mensual, name="recaudacion_mensual"),
    path(
        "recaudacion-mensual/excel/",
        views.exportar_recaudacion_mensual_excel,
        name="recaudacion_mensual_excel"
    ),
    path(
        "cartera-vencida/",
        views.cartera_vencida,
        name="cartera_vencida"
    ),
    path(
        "cartera-vencida/excel/",
        views.exportar_cartera_vencida_excel,
        name="cartera_vencida_excel"
    ),
]