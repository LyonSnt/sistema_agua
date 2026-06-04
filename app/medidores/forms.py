from django import forms
from .models import Medidor


class MedidorForm(forms.ModelForm):
    class Meta:
        model = Medidor
        fields = [
            "abonado",
            "numero",
            "marca",
            "modelo",
            "lectura_inicial",
            "fecha_instalacion",
            "estado",
            "observacion",
        ]

        widgets = {
            "abonado": forms.Select(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "numero": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "marca": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "modelo": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "lectura_inicial": forms.NumberInput(attrs={
                "class": "w-full px-4 py-2 border rounded-lg",
                "step": "0.01",
                "onwheel": "this.blur()",
            }),
            "fecha_instalacion": forms.DateInput(attrs={
                "type": "date",
                "class": "w-full px-4 py-2 border rounded-lg",
            }),
            "estado": forms.Select(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "observacion": forms.Textarea(attrs={
                "class": "w-full px-4 py-2 border rounded-lg",
                "rows": 3,
            }),
        }