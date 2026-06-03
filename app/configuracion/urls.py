"""
URL configuration for configuracion project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from usuarios.views import LoginAuditoriaView, LogoutAuditoriaView

urlpatterns = [
    path('admin/', admin.site.urls),
    path("panel/", include("panel.urls")),
    path("abonados/", include("abonados.urls")),
    path("facturacion/", include("facturacion.urls")),
    path("pagos/", include("pagos.urls")),
    path("reportes/", include("reportes.urls")),
    path("lecturas/", include("lecturas.urls")),
    path("login/", LoginAuditoriaView.as_view(), name="login"),
    path("logout/", LogoutAuditoriaView.as_view(), name="logout"),
    path("multas/", include("multas.urls")),
    path("servicios/", include("servicios.urls")),
]
