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
    path(
        "comprobante/<int:pago_id>/pdf/",
        views.comprobante_pago_pdf,
        name="comprobante_pdf"
    ),
    path("exitoso/<int:pago_id>/", views.pago_exitoso, name="pago_exitoso"),
    path(
        "comprobante/<int:pago_id>/imprimir/",
        views.comprobante_pago_imprimir,
        name="comprobante_imprimir"
    ),
    path(
        "ticket/<int:pago_id>/",
        views.ticket_pago,
        name="ticket_pago"
    ),
]