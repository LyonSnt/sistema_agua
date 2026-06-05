from django import forms

from .models import SuspensionServicio


class SuspenderServicioForm(forms.ModelForm):
    class Meta:
        model = SuspensionServicio
        fields = [
            "abonado",
            "fecha_suspension",
            "motivo_suspension",
        ]


class ReconectarServicioForm(forms.ModelForm):
    fecha_reconexion = forms.DateField(required=True)

    class Meta:
        model = SuspensionServicio
        fields = [
            "fecha_reconexion",
            "observacion_reconexion",
        ]
