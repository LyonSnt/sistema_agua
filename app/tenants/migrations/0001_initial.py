# Generated manually for tenant registry setup.

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("actualizado_en", models.DateTimeField(auto_now=True)),
                ("activo", models.BooleanField(default=True)),
                ("slug", models.SlugField(max_length=50, unique=True, validators=[django.core.validators.RegexValidator(message="Use solo minusculas, numeros y guiones.", regex="^[a-z0-9-]+$")])),
                ("nombre", models.CharField(max_length=150)),
                ("db_name", models.CharField(blank=True, max_length=100, unique=True)),
            ],
            options={
                "verbose_name": "Tenant",
                "verbose_name_plural": "Tenants",
                "ordering": ["nombre"],
            },
        ),
    ]
