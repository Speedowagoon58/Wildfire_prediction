from django.urls import path
from . import views

app_name = "historical_data"

urlpatterns = [
    path("", views.index, name="index"),
    path(
        "api/historical-fires/", views.get_historical_fires, name="get_historical_fires"
    ),
]
