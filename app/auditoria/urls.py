from django.urls import path

from . import views

app_name = "auditoria"

urlpatterns = [
    path("", views.lista_auditoria, name="lista"),
    path("exportar-excel/", views.exportar_auditoria_excel, name="exportar_excel"),
]
