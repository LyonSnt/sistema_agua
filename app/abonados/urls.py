from django.urls import path
from . import views

app_name = "abonados"

urlpatterns = [
    path("", views.lista_abonados, name="lista"),
    path("crear/", views.crear_abonado, name="crear"),
    path("<int:abonado_id>/detalle/", views.detalle_abonado, name="detalle"),
    path("<int:abonado_id>/editar/", views.editar_abonado, name="editar"),
    path("<int:abonado_id>/estado/", views.cambiar_estado_abonado, name="cambiar_estado"),
    path("<int:abonado_id>/pdf/", views.detalle_abonado_pdf, name="detalle_pdf"),
]
