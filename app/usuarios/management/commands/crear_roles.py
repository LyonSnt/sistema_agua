from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Crea los roles base del sistema"

    def handle(self, *args, **kwargs):
        roles = [
            "Administrador",
            "Cajero",
            "Lecturista",
            "Supervisor",
            "Consulta",
        ]

        for nombre in roles:
            Group.objects.get_or_create(name=nombre)

        self.stdout.write(
            self.style.SUCCESS("Roles creados correctamente.")
        )