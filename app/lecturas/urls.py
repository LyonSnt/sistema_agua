from django.urls import path
from . import views

app_name = "lecturas"

urlpatterns = [
    path("generar/", views.generar_lecturas, name="generar"),
    path("registro-masivo/", views.registro_masivo_lecturas, name="registro_masivo"),
    path("plantilla-excel/", views.descargar_plantilla_lecturas, name="plantilla_excel"),
    path("importar-excel/", views.importar_lecturas_excel, name="importar_excel"),
]