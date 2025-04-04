from django.db import migrations
from django.utils import timezone
from datetime import timedelta
import random


def add_initial_weather_data(apps, schema_editor):
    Region = apps.get_model("core", "Region")
    WeatherData = apps.get_model("weather", "WeatherData")

    # Get current time
    now = timezone.now()

    # For each region, create 30 days of weather data
    for region in Region.objects.all():
        for days_ago in range(30, -1, -1):  # 30 days ago to today
            # Base temperature varies by elevation
            base_temp = max(
                10, 30 - (region.elevation / 1000) * 5
            )  # Lower temp at higher elevation

            # Create weather data with some random variation
            timestamp = now - timedelta(days=days_ago)
            WeatherData.objects.create(
                region=region,
                timestamp=timestamp,
                temperature=base_temp
                + random.uniform(-5, 5),  # Random variation in temperature
                humidity=random.uniform(30, 70),  # Humidity between 30-70%
                wind_speed=random.uniform(0, 15),  # Wind speed 0-15 m/s
                wind_direction=random.uniform(0, 360),  # Wind direction 0-360 degrees
                precipitation=(
                    random.uniform(0, 10) if random.random() > 0.7 else 0
                ),  # 30% chance of rain
                pressure=random.uniform(980, 1020),  # Atmospheric pressure
            )


def remove_initial_weather_data(apps, schema_editor):
    WeatherData = apps.get_model("weather", "WeatherData")
    WeatherData.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("weather", "0001_initial"),
        ("core", "0002_initial_regions"),
    ]

    operations = [
        migrations.RunPython(add_initial_weather_data, remove_initial_weather_data),
    ]
