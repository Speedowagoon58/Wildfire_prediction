from django.urls import path
from . import views

app_name = "mapping"

urlpatterns = [
    path("api/regions/", views.get_regions, name="get_regions"),
]
