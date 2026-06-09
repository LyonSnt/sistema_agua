# Generated manually for short institutional display name.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("configuracion_institucional", "0002_configuracioninstitucional_cargo_representante_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="configuracioninstitucional",
            name="nombre_corto",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
