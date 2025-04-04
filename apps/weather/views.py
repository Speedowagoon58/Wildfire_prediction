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

    @action(detail=False, methods=["get"])
    def historical_data(self, request):
        """
        Fetch historical weather data for a region within a date range.
        """
        region_id = request.query_params.get("region_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not all([region_id, start_date, end_date]):
            return Response(
                {"error": "Region ID, start date, and end date are required"},
                status=400,
            )

        try:
            region = Region.objects.get(id=region_id)
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")

            # Fetch historical data from NOAA
            historical_data = fetch_historical_weather(region, start_date, end_date)

            if not historical_data:
                return Response(
                    {"error": "No historical data available for the specified period"},
                    status=404,
                )

            return Response(historical_data)

        except Region.DoesNotExist:
            return Response({"error": "Region not found"}, status=404)
        except ValueError:
            return Response(
                {"error": "Invalid date format. Use YYYY-MM-DD"}, status=400
            )
        except Exception as e:
            return Response(
                {"error": f"Error fetching historical data: {str(e)}"}, status=500
            )
