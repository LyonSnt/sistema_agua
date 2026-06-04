from django.urls import path
from . import views

app_name = "abonados"

urlpatterns = [
    path("", views.lista_abonados, name="lista"),
    path("<int:abonado_id>/detalle/", views.detalle_abonado, name="detalle"),
    path("<int:abonado_id>/pdf/", views.detalle_abonado_pdf, name="detalle_pdf"),
]