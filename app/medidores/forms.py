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


class CambioMedidorForm(forms.Form):
    fecha_cambio = forms.DateField(
        label="Fecha de cambio",
        widget=forms.DateInput(attrs={
            "type": "date",
            "class": "w-full px-4 py-2 border rounded-lg",
        }),
    )
    lectura_final_anterior = forms.DecimalField(
        label="Lectura final del medidor anterior",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
            "step": "0.01",
            "onwheel": "this.blur()",
        }),
    )
    numero_nuevo = forms.CharField(
        label="Número del medidor nuevo",
        max_length=50,
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
        }),
    )
    marca_nuevo = forms.CharField(
        label="Marca del medidor nuevo",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
        }),
    )
    modelo_nuevo = forms.CharField(
        label="Modelo del medidor nuevo",
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
        }),
    )
    lectura_inicial_nuevo = forms.DecimalField(
        label="Lectura inicial del medidor nuevo",
        min_value=0,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
            "step": "0.01",
            "onwheel": "this.blur()",
        }),
    )
    motivo = forms.CharField(
        label="Motivo",
        widget=forms.Textarea(attrs={
            "class": "w-full px-4 py-2 border rounded-lg",
            "rows": 3,
        }),
    )

    def __init__(self, *args, medidor_anterior=None, **kwargs):
        self.medidor_anterior = medidor_anterior
        super().__init__(*args, **kwargs)

    def clean_numero_nuevo(self):
        numero = self.cleaned_data["numero_nuevo"].strip()

        if Medidor.objects.filter(numero=numero).exists():
            raise forms.ValidationError(
                "Ya existe un medidor con este número."
            )

        return numero

    def clean_lectura_final_anterior(self):
        lectura = self.cleaned_data["lectura_final_anterior"]

        if (
            self.medidor_anterior
            and lectura < self.medidor_anterior.lectura_inicial
        ):
            raise forms.ValidationError(
                "La lectura final no puede ser menor que la lectura inicial del medidor anterior."
            )

        return lectura
