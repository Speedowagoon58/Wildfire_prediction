import requests
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from .models import WeatherData


def fetch_current_weather(region):
    """
    Fetch current weather data from OpenWeatherMap API for a given region
    """
    params = {
        "lat": region.latitude,
        "lon": region.longitude,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric",  # Use metric units
    }

    try:
        response = requests.get(settings.OPENWEATHERMAP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Convert OpenWeatherMap data to our format
        weather_data = WeatherData.objects.create(
            region=region,
            timestamp=timezone.now(),
            temperature=data["main"]["temp"],
            humidity=data["main"]["humidity"],
            wind_speed=data["wind"]["speed"],
            wind_direction=data["wind"].get("deg", 0),
            precipitation=data.get("rain", {}).get("1h", 0),  # Rain in last hour
            pressure=data["main"]["pressure"],
        )

        return weather_data

    except requests.RequestException as e:
        print(f"Error fetching weather data for {region.name}: {str(e)}")
        return None


def update_weather_data():
    """
    Update weather data for all regions
    """
    from apps.core.models import Region

    for region in Region.objects.all():
        fetch_current_weather(region)
