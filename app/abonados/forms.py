from django import forms

from .models import Abonado, Ruta, Sector


class AbonadoForm(forms.ModelForm):
    class Meta:
        model = Abonado
        fields = [
            "codigo",
            "cedula_ruc",
            "nombres",
            "apellidos",
            "telefono",
            "correo",
            "direccion",
            "referencia",
            "sector",
            "ruta",
        ]

        widgets = {
            "codigo": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "cedula_ruc": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "nombres": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "apellidos": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "telefono": forms.TextInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "correo": forms.EmailInput(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "direccion": forms.Textarea(attrs={"class": "w-full px-4 py-2 border rounded-lg", "rows": 3}),
            "referencia": forms.Textarea(attrs={"class": "w-full px-4 py-2 border rounded-lg", "rows": 3}),
            "sector": forms.Select(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
            "ruta": forms.Select(attrs={"class": "w-full px-4 py-2 border rounded-lg"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["sector"].queryset = Sector.objects.filter(activo=True)
        self.fields["ruta"].queryset = Ruta.objects.select_related(
            "sector"
        ).filter(
            activo=True,
            sector__activo=True,
        )

    def clean(self):
        cleaned_data = super().clean()
        sector = cleaned_data.get("sector")
        ruta = cleaned_data.get("ruta")

        if sector and ruta and ruta.sector_id != sector.id:
            self.add_error(
                "ruta",
                "La ruta seleccionada no pertenece al sector indicado."
            )

        return cleaned_data
