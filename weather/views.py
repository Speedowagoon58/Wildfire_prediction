from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.conf import settings


def index(request):
    return render(request, "weather/index.html")


def get_weather_data(request, region_id):
    # TODO: Replace with actual region data
    # For now, using a sample region (Casablanca)
    lat = 33.5731
    lon = -7.5898

    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return JsonResponse(
            {"error": "OpenWeatherMap API key not configured"}, status=500
        )

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        data = response.json()

        return JsonResponse(
            {
                "temperature": data["main"]["temp"],
                "humidity": data["main"]["humidity"],
                "windSpeed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
            }
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
