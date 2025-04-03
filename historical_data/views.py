from django.shortcuts import render
from django.http import JsonResponse


def index(request):
    return render(request, "historical_data/index.html")


def get_historical_fires(request):
    # TODO: Replace with actual historical data from database
    fires = [
        {
            "id": 1,
            "location": "Casablanca",
            "date": "2023-07-15",
            "area_affected": "500 hectares",
            "lat": 33.5731,
            "lng": -7.5898,
        }
    ]
    return JsonResponse({"fires": fires})
