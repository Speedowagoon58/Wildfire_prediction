from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
import requests
from requests.exceptions import RequestException
from datetime import datetime, timedelta
from django.utils import timezone
from .models import WeatherData
from .serializers import WeatherDataSerializer
from apps.core.models import Region
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def calculate_wildfire_risk(temperature, humidity, wind_speed, precipitation):
    """Calculate wildfire risk based on weather conditions"""
    risk_score = 0

    # Temperature contribution (higher temp = higher risk)
    if temperature > 30:
        risk_score += 3
    elif temperature > 25:
        risk_score += 2
    elif temperature > 20:
        risk_score += 1

    # Humidity contribution (lower humidity = higher risk)
    if humidity < 30:
        risk_score += 3
    elif humidity < 50:
        risk_score += 2
    elif humidity < 70:
        risk_score += 1

    # Wind speed contribution (higher wind = higher risk)
    if wind_speed > 20:
        risk_score += 3
    elif wind_speed > 15:
        risk_score += 2
    elif wind_speed > 10:
        risk_score += 1

    # Precipitation contribution (no rain = higher risk)
    if precipitation == 0:
        risk_score += 2

    # Normalize risk score to 0-100
    risk_score = (risk_score / 11) * 100

    # Determine risk level and color
    if risk_score >= 70:
        return "High", "red"
    elif risk_score >= 40:
        return "Medium", "orange"
    else:
        return "Low", "green"


class WeatherViewSet(viewsets.ModelViewSet):
    queryset = WeatherData.objects.all()
    serializer_class = WeatherDataSerializer

    @action(detail=False, methods=["get"])
    def fetch_current_weather(self, request):
        region_id = request.query_params.get("region_id")
        if not region_id:
            return Response({"error": "Region ID is required"}, status=400)

        try:
            region = Region.objects.get(id=region_id)
        except Region.DoesNotExist:
            return Response({"error": "Region not found"}, status=404)

        api_key = settings.WEATHER_API_KEY
        if not api_key:
            logger.error("Weather API key is not configured.")
            return Response(
                {"error": "Weather service configuration error"}, status=500
            )

        url = f"{settings.WEATHER_API_URL}?lat={region.latitude}&lon={region.longitude}&appid={api_key}&units=metric"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            main_data = data.get("main", {})
            wind_data = data.get("wind", {})
            rain_data = data.get("rain", {})

            temperature = main_data.get("temp")
            humidity = main_data.get("humidity")
            pressure = main_data.get("pressure")
            wind_speed = wind_data.get("speed")
            wind_direction = wind_data.get("deg")
            precipitation = rain_data.get("1h", 0)

            if (
                temperature is None
                or humidity is None
                or pressure is None
                or wind_speed is None
            ):
                logger.error(f"Incomplete weather data received from API: {data}")
                return Response(
                    {"error": "Incomplete data from weather service"}, status=500
                )

            weather_data = WeatherData.objects.create(
                region=region,
                timestamp=timezone.now(),
                temperature=temperature,
                humidity=humidity,
                wind_speed=wind_speed,
                wind_direction=wind_direction,
                precipitation=precipitation,
                pressure=pressure,
            )

            return Response(WeatherDataSerializer(weather_data).data)

        except RequestException as e:
            logger.error(f"Error fetching weather data from API: {e}")
            return Response(
                {"error": "Could not connect to weather service"}, status=503
            )
        except (KeyError, TypeError, ValueError) as e:
            logger.error(f"Error processing weather data: {e} - Data: {data}")
            return Response({"error": "Error processing weather data"}, status=500)
        except Exception as e:
            logger.exception(
                f"An unexpected error occurred while fetching weather data for region {region_id}"
            )
            return Response({"error": "An unexpected error occurred"}, status=500)


def dashboard(request):
    regions = Region.objects.all()
    weather_data = []

    for region in regions:
        # Get latest weather data for the region
        latest_weather = (
            WeatherData.objects.filter(region=region).order_by("-timestamp").first()
        )

        if latest_weather:
            risk_level, risk_color = calculate_wildfire_risk(
                latest_weather.temperature,
                latest_weather.humidity,
                latest_weather.wind_speed,
                latest_weather.precipitation,
            )

            weather_data.append(
                {
                    "region": region,
                    "weather": latest_weather,
                    "risk_level": risk_level,
                    "risk_color": risk_color,
                }
            )

    return render(request, "weather/dashboard.html", {"weather_data": weather_data})
