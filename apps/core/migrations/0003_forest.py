# Generated manually

from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MinValueValidator, MaxValueValidator


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_initial_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="Forest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100)),
                (
                    "area",
                    models.FloatField(help_text="Area in square kilometers"),
                ),
                (
                    "dominant_species",
                    models.CharField(help_text="Dominant tree species", max_length=100),
                ),
                (
                    "density",
                    models.FloatField(
                        help_text="Forest density (0-1)",
                        validators=[
                            MinValueValidator(0.0),
                            MaxValueValidator(1.0),
                        ],
                    ),
                ),
                ("description", models.TextField(blank=True)),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True),
                ),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="forests",
                        to="core.region",
                    ),
                ),
            ],
        ),
    ]
