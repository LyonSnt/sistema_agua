from django.db import models

class ConfiguracionInstitucional(models.Model):
    nombre = models.CharField(max_length=200)
    nombre_corto = models.CharField(max_length=100, blank=True)
    ruc = models.CharField(max_length=20, blank=True)
    direccion = models.CharField(max_length=250, blank=True)
    telefono = models.CharField(max_length=50, blank=True)
    correo = models.EmailField(blank=True)
    logo = models.ImageField(upload_to="logos/", null=True, blank=True)

    representante = models.CharField(max_length=150, blank=True)
    cargo_representante = models.CharField(max_length=100, blank=True)

    responsable_caja = models.CharField(max_length=150, blank=True)
    cargo_responsable_caja = models.CharField(max_length=100, blank=True)

    pie_pagina = models.TextField(blank=True)

    class Meta:
        verbose_name = "Configuración institucional"
        verbose_name_plural = "Configuración institucional"

    def __str__(self):
        return self.nombre
