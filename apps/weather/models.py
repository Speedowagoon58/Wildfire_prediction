from django.db import models
from apps.core.models import Region


class WeatherData(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE)
    timestamp = models.DateTimeField()
    temperature = models.FloatField(help_text="Temperature in Celsius")
    humidity = models.FloatField(help_text="Relative humidity in percentage")
    wind_speed = models.FloatField(help_text="Wind speed in meters per second")
    wind_direction = models.FloatField(
        help_text="Wind direction in degrees", null=True, blank=True
    )
    precipitation = models.FloatField(help_text="Precipitation in millimeters")
    pressure = models.FloatField(help_text="Atmospheric pressure in hPa")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["region", "timestamp"])]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Weather data for {self.region.name} at {self.timestamp}"
