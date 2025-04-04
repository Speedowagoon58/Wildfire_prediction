from django.db import migrations
from datetime import datetime, timedelta
import random


def add_initial_weather_data(apps, schema_editor):
    Region = apps.get_model("core", "Region")
    WeatherData = apps.get_model("weather", "WeatherData")

    # Get all regions
    regions = Region.objects.all()

    # Create 30 days of weather data for each region
    for region in regions:
        base_temp = (
            25 - (region.elevation / 1000) * 6
        )  # Temperature decreases with elevation

        for days_ago in range(30):
            current_time = datetime.now() - timedelta(days=days_ago)

            # Add random variations
            temp_variation = random.uniform(-5, 5)
            humidity_variation = random.uniform(-10, 10)
            wind_speed_variation = random.uniform(-5, 5)
            wind_dir_variation = random.uniform(0, 360)
            precip_variation = random.uniform(0, 10)
            pressure_variation = random.uniform(-10, 10)

            WeatherData.objects.create(
                region=region,
                timestamp=current_time,
                temperature=base_temp + temp_variation,
                humidity=60 + humidity_variation,
                wind_speed=10 + wind_speed_variation,
                wind_direction=180 + wind_dir_variation,
                precipitation=5 + precip_variation,
                pressure=1013 + pressure_variation,
            )


def remove_initial_weather_data(apps, schema_editor):
    WeatherData = apps.get_model("weather", "WeatherData")
    WeatherData.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("weather", "0001_initial"),
        ("core", "0002_initial_data"),
    ]

    operations = [
        migrations.RunPython(add_initial_weather_data, remove_initial_weather_data),
    ]
