from rest_framework import serializers
from .models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "description",
            "latitude",
            "longitude",
            "area",
            "population",
            "soil_type",
            "vegetation_density",
            "climate_zone",
        ]
