from django.contrib import admin
from .models import Region, SoilType


@admin.register(SoilType)
class SoilTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "fire_risk_factor", "moisture_retention", "organic_matter")
    search_fields = ("name", "description")
    list_filter = ("fire_risk_factor",)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "latitude",
        "longitude",
        "elevation",
        "soil_type",
        "vegetation_density",
    )
    search_fields = ("name",)
    list_filter = ("soil_type",)
    autocomplete_fields = ["soil_type"]
