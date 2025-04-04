from rest_framework import serializers
from .models import WildfirePrediction


class WildfirePredictionSerializer(serializers.ModelSerializer):
    # Optionally make some fields read-only if they shouldn't be set directly via API
    # region = serializers.PrimaryKeyRelatedField(read_only=True)
    # prediction_date = serializers.DateTimeField(read_only=True)
    # created_at = serializers.DateTimeField(read_only=True)
    # model_version = serializers.CharField(read_only=True)
    # features_used = serializers.JSONField(read_only=True)

    class Meta:
        model = WildfirePrediction
        fields = "__all__"
        # Example of read_only_fields:
        # read_only_fields = ('prediction_date', 'created_at', 'model_version', 'features_used')
