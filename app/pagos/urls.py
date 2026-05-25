from django.urls import path
from . import views

app_name = "pagos"

urlpatterns = [
    path("cobrar/<int:factura_id>/", views.cobrar_factura, name="cobrar"),
    path("comprobante/<int:pago_id>/", views.comprobante_pago, name="comprobante"),
    path(
        "anular/<int:pago_id>/",
        views.anular_pago,
        name="anular"
    ),
]