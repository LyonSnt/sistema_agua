from django.urls import path
from . import views

app_name = "facturacion"

urlpatterns = [
    path("pendientes/", views.facturas_pendientes, name="pendientes"),
    path("factura/<int:factura_id>/", views.detalle_factura, name="detalle"),
    path("generar/", views.generar_facturacion_periodo, name="generar"),
    path("factura/<int:factura_id>/anular/", views.anular_factura, name="anular"),
]