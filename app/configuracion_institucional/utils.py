from .models import ConfiguracionInstitucional


def obtener_configuracion():
    return ConfiguracionInstitucional.objects.first()