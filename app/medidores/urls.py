from django.urls import path
from . import views

app_name = "medidores"

urlpatterns = [
    path("", views.lista_medidores, name="lista"),
    path("crear/", views.crear_medidor, name="crear"),
    path("<int:medidor_id>/detalle/", views.detalle_medidor, name="detalle"),
    path("<int:medidor_id>/editar/", views.editar_medidor, name="editar"),
    path("<int:medidor_id>/cambiar/", views.cambiar_medidor, name="cambiar"),
    path("<int:medidor_id>/pdf/", views.detalle_medidor_pdf, name="detalle_pdf"),
]
