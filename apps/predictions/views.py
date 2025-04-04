from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import WildfirePrediction
from .serializers import WildfirePredictionSerializer
from .ml_model import WildfirePredictionModel
from apps.core.models import Region
from apps.weather.models import WeatherData
import logging

logger = logging.getLogger(__name__)

# Instantiate the model (consider how this is managed in a production environment - singleton?)
# This will attempt to load the pre-trained model when the Django process starts.
# prediction_model = WildfirePredictionModel() # DEFER INSTANTIATION


class PredictionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet to view wildfire predictions."""

    queryset = WildfirePrediction.objects.all()
    serializer_class = WildfirePredictionSerializer
    _prediction_model_instance = None  # Class variable to hold the singleton instance

    @classmethod
    def get_prediction_model(cls):
        """Lazy loads the prediction model as a singleton."""
        if cls._prediction_model_instance is None:
            print(
                "Instantiating WildfirePredictionModel..."
            )  # Add print statement for debugging
            cls._prediction_model_instance = WildfirePredictionModel()
        return cls._prediction_model_instance

    @action(detail=False, methods=["post"], url_path="predict-for-region")
    def predict_for_region(self, request):
        """
        Triggers a wildfire risk prediction for a given region based on the latest weather data.
        Expects {"region_id": <id>} in the request body.
        """
        # Get the model instance lazily
        model = self.get_prediction_model()

        region_id = request.data.get("region_id")
        if not region_id:
            return Response(
                {"error": "Region ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        region = get_object_or_404(Region, pk=region_id)

        # 1. Fetch latest relevant weather data for the region
        #    For simplicity, using the very latest record. A real model might need a sequence.
        try:
            latest_weather = WeatherData.objects.filter(region=region).latest(
                "timestamp"
            )
        except WeatherData.DoesNotExist:
            logger.warning(
                f"No weather data found for region {region_id} to make prediction."
            )
            return Response(
                {"error": "Insufficient weather data for prediction"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 2. Prepare features
        try:
            features = model.prepare_features(
                latest_weather
            )  # Use the local 'model' instance
        except Exception as e:
            logger.error(f"Error preparing features for region {region_id}: {e}")
            return Response(
                {"error": "Error preparing features for prediction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 3. Get prediction
        risk_prob, confidence = model.predict(
            features
        )  # Use the local 'model' instance

        if risk_prob is None or confidence is None:
            logger.error(
                f"Prediction failed for region {region_id}. Model might not be ready or an error occurred."
            )
            return Response(
                {"error": "Prediction generation failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 4. Convert probability to risk level
        #    (This threshold logic is illustrative and needs tuning based on model output)
        if risk_prob < 0.25:
            risk_level = WildfirePrediction.LOW
        elif risk_prob < 0.5:
            risk_level = WildfirePrediction.MEDIUM
        elif risk_prob < 0.75:
            risk_level = WildfirePrediction.HIGH
        else:
            risk_level = WildfirePrediction.EXTREME

        # 5. Save the prediction
        #    Using update_or_create to avoid duplicate predictions for the exact same time?
        #    Or maybe always create a new one? Decided to always create for this example.
        try:
            prediction = WildfirePrediction.objects.create(
                region=region,
                prediction_date=timezone.now(),  # Prediction is made now for the state reflected by latest_weather
                risk_level=risk_level,
                confidence=confidence,
                features_used=features,  # Store the features used
                model_version=model.version,  # Use the local 'model' instance
            )
        except Exception as e:
            logger.exception(f"Error saving prediction for region {region_id}")
            return Response(
                {"error": "Failed to save prediction result"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 6. Return the result
        serializer = self.get_serializer(prediction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


def dashboard(request):
    return render(request, "predictions/dashboard.html")
