from django.urls import path
from . import views

app_name = "weather"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "api/weather/<int:region_id>/", views.get_weather_data, name="get_weather_data"
    ),
]
