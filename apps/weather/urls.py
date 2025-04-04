from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WeatherViewSet, dashboard

app_name = "weather"

router = DefaultRouter()
router.register(r"data", WeatherViewSet, basename="weatherdata")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("api/", include(router.urls)),
]
