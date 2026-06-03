from django.urls import path
from . import views

app_name = "abonados"

urlpatterns = [
    path("", views.lista_abonados, name="lista"),
    path("<int:abonado_id>/detalle/", views.detalle_abonado, name="detalle"),
]