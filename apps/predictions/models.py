from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import Region


class WildfirePrediction(models.Model):
    """Model for storing wildfire risk predictions."""

    # Define risk level choices as constants
    LOW_RISK = "low"
    MEDIUM_RISK = "medium"
    HIGH_RISK = "high"

    RISK_CHOICES = [
        (LOW_RISK, "Low Risk"),
        (MEDIUM_RISK, "Medium Risk"),
        (HIGH_RISK, "High Risk"),
    ]

    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    prediction_date = models.DateTimeField(
        help_text="The date and time for which the prediction is made"
    )
    risk_level = models.CharField(
        max_length=20,
        choices=RISK_CHOICES,
        default=MEDIUM_RISK,
        help_text="Current wildfire risk level",
    )
    confidence = models.FloatField(
        help_text="Prediction confidence score (0-100)",
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
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

    def get_risk_level_display(self):
        """Get the display value for the risk level."""
        return dict(self.RISK_CHOICES).get(self.risk_level, self.risk_level)
