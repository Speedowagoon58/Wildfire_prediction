from django.http import JsonResponse


def get_regions(request):
    # TODO: Replace with actual region data from database
    regions = [
        {"id": 1, "name": "Casablanca", "lat": 33.5731, "lng": -7.5898},
        {"id": 2, "name": "Rabat", "lat": 34.0209, "lng": -6.8416},
        {"id": 3, "name": "Marrakech", "lat": 31.6295, "lng": -7.9811},
    ]
    return JsonResponse({"regions": regions})
