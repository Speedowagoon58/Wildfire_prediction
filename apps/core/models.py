from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class SoilType(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    fire_risk_factor = models.FloatField(
        help_text="Multiplier for wildfire risk based on soil type (0.5-2.0)",
        default=1.0,
    )
    moisture_retention = models.FloatField(
        help_text="Soil's ability to retain moisture (0-1)", default=0.5
    )
    organic_matter = models.FloatField(
        help_text="Percentage of organic matter in soil", default=2.0
    )

    def __str__(self):
        return self.name


class Region(models.Model):
    CLIMATE_ZONES = [
        ("mediterranean", "Mediterranean"),
        ("semi_arid", "Semi-Arid"),
        ("temperate", "Temperate"),
    ]

    name = models.CharField(max_length=100)
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation = models.FloatField(help_text="Elevation in meters")
    area = models.FloatField(help_text="Area in square kilometers")
    population = models.IntegerField(help_text="Population in the region")
    soil_type = models.ForeignKey(
        SoilType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Predominant soil type in the region",
    )
    vegetation_density = models.FloatField(
        help_text="Vegetation density (0-1)",
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    climate_zone = models.CharField(
        max_length=20,
        choices=CLIMATE_ZONES,
        default="mediterranean",
        help_text="Climate zone classification for the region",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name="cities")
    latitude = models.FloatField()
    longitude = models.FloatField()
    population = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return f"{self.name} ({self.region.name})"


class WildfireEvent(models.Model):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    EXTREME = 4
    SEVERITY_CHOICES = [
        (LOW, "Low"),
        (MEDIUM, "Medium"),
        (HIGH, "High"),
        (EXTREME, "Extreme"),
    ]

    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    severity = models.IntegerField(choices=SEVERITY_CHOICES)
    area_affected = models.FloatField(help_text="Area affected in square kilometers")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        pass

    def __str__(self):
        return f"Wildfire at {self.region.name} on {self.start_date.date()}"


class Forest(models.Model):
    name = models.CharField(max_length=100)
    region = models.ForeignKey(
        "Region", on_delete=models.CASCADE, related_name="forests"
    )
    area = models.FloatField(help_text="Area in square kilometers")
    dominant_species = models.CharField(
        max_length=100, help_text="Dominant tree species"
    )
    density = models.FloatField(
        help_text="Forest density (0-1)",
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.region.name})"
