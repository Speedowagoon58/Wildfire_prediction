# Generated by Django 5.0.1 on 2025-04-04 14:20

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("core", "0002_initial_data"),
    ]

    operations = [
        migrations.CreateModel(
            name="WildfirePrediction",
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
                (
                    "prediction_date",
                    models.DateTimeField(
                        help_text="The date and time for which the prediction is made"
                    ),
                ),
                (
                    "risk_level",
                    models.IntegerField(
                        choices=[(1, "Low"), (2, "Medium"), (3, "High"), (4, "Extreme")]
                    ),
                ),
                (
                    "confidence",
                    models.FloatField(
                        help_text="Prediction confidence score (0-1)",
                        validators=[
                            django.core.validators.MinValueValidator(0.0),
                            django.core.validators.MaxValueValidator(1.0),
                        ],
                    ),
                ),
                (
                    "features_used",
                    models.JSONField(help_text="Features used in the prediction"),
                ),
                ("model_version", models.CharField(max_length=50)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "region",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="core.region"
                    ),
                ),
            ],
            options={
                "ordering": ["-prediction_date"],
                "indexes": [
                    models.Index(
                        fields=["region", "prediction_date"],
                        name="predictions_region__dcc8f1_idx",
                    )
                ],
            },
        ),
    ]
