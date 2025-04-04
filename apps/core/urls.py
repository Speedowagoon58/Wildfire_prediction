from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("regions/", views.region_list, name="regions"),
    path("region/<int:pk>/", views.region_detail, name="region_detail"),
]
