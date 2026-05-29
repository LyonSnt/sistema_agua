from django.urls import path
from . import views

app_name = "servicios"

urlpatterns = [
    path("", views.lista_suspensiones, name="lista"),
    path("suspender/", views.suspender_servicio, name="suspender"),
    path("<int:suspension_id>/reconectar/", views.reconectar_servicio, name="reconectar"),
    path("abonado/<int:abonado_id>/reconectar/", views.reconectar_por_abonado, name="reconectar_por_abonado"),
    
]