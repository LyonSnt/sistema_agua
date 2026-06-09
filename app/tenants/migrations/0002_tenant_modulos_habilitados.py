# Generated manually for tenant module configuration.

from django.db import migrations, models

import tenants.modules


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="modulos_habilitados",
            field=models.JSONField(default=tenants.modules.modulos_por_defecto),
        ),
    ]
