from django.urls import path
from . import views

app_name = "abonados"

urlpatterns = [
    path("", views.lista_abonados, name="lista"),
]