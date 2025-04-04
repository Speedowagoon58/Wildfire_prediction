from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import Region


class WildfirePrediction(models.Model):
    # Define risk level choices as constants
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    RISK_CHOICES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (EXTREME, "Extreme"),
    ]

    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField(
        help_text="The date and time for which the prediction is made"
    )
    risk_level = models.IntegerField(choices=RISK_CHOICES)
    confidence = models.FloatField(
        help_text="Prediction confidence score (0-1)",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    features_used = models.JSONField(help_text="Features used in the prediction")
    model_version = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # app_label = "predictions" # Removed redundant app_label
        indexes = [models.Index(fields=["region", "prediction_date"])]
        # Add default ordering
        ordering = ["-prediction_date"]

    def __str__(self):
        return f"Wildfire prediction for {self.region.name} on {self.prediction_date}"
