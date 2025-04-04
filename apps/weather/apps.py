from django.apps import AppConfig
import os


class WeatherConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.weather"
    path = os.path.dirname(os.path.abspath(__file__))
