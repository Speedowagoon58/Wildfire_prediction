from django.apps import AppConfig
import os


class PredictionsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.predictions"
    path = os.path.dirname(os.path.abspath(__file__))
