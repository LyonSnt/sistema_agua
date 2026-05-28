from django.urls import path
from . import views

app_name = "multas"

urlpatterns = [
    path("", views.lista_multas, name="lista"),
    path("crear/", views.crear_multa, name="crear"),
    path("<int:multa_id>/cobrar/", views.cobrar_multa, name="cobrar"),
    path("<int:multa_id>/anular/", views.anular_multa, name="anular"),
    path("<int:multa_id>/comprobante-pdf/", views.comprobante_multa_pdf, name="comprobante_pdf"),
    path("reporte/", views.reporte_multas, name="reporte"),
    path("reporte/excel/", views.exportar_reporte_multas_excel, name="reporte_excel"),
]