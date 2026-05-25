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
]