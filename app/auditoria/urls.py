from django.urls import path

from . import views

app_name = "auditoria"

urlpatterns = [
    path("", views.lista_auditoria, name="lista"),
]
