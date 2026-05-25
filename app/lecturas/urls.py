from django.urls import path
from . import views

app_name = "lecturas"

urlpatterns = [
    path("generar/", views.generar_lecturas, name="generar"),
    path("registro-masivo/", views.registro_masivo_lecturas, name="registro_masivo"),
]