from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta
import random
import logging

from .models import WildfirePrediction
from .serializers import WildfirePredictionSerializer
from .ml_model import WildfirePredictionModel
from apps.core.models import Region
from apps.weather.models import WeatherData
from apps.weather.services import fetch_current_weather

logger = logging.getLogger(__name__)

# Instantiate the model (consider how this is managed in a production environment - singleton?)
# This will attempt to load the pre-trained model when the Django process starts.
# prediction_model = WildfirePredictionModel() # DEFER INSTANTIATION


def analyze_historical_patterns(region):
    """Analyze historical weather patterns and their correlation with wildfire events."""
    # Get weather data from the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    historical_data = WeatherData.objects.filter(
        region=region, timestamp__gte=thirty_days_ago
    ).order_by("timestamp")

    # Calculate averages and trends
    if not historical_data.exists():
        return None

    # Calculate average values
    avg_temperature = sum(data.temperature for data in historical_data) / len(
        historical_data
    )
    avg_humidity = sum(data.humidity for data in historical_data) / len(historical_data)
    avg_wind_speed = sum(data.wind_speed for data in historical_data) / len(
        historical_data
    )
    avg_precipitation = sum(data.precipitation for data in historical_data) / len(
        historical_data
    )

    # Calculate trends (simple linear regression)
    temps = [(data.timestamp, data.temperature) for data in historical_data]
    humidities = [(data.timestamp, data.humidity) for data in historical_data]

    # Calculate temperature trend
    if len(temps) > 1:
        temp_trend = (temps[-1][1] - temps[0][1]) / (
            temps[-1][0] - temps[0][0]
        ).total_seconds()
    else:
        temp_trend = 0

    # Calculate humidity trend
    if len(humidities) > 1:
        humidity_trend = (humidities[-1][1] - humidities[0][1]) / (
            humidities[-1][0] - humidities[0][0]
        ).total_seconds()
    else:
        humidity_trend = 0

    # Calculate drought index (simplified)
    total_precipitation = sum(data.precipitation for data in historical_data)
    potential_evaporation = sum(
        data.temperature * 0.5 for data in historical_data
    )  # Simplified calculation
    drought_index = (
        potential_evaporation - total_precipitation
    ) / 30  # Average daily drought index

    return {
        "avg_temperature": avg_temperature,
        "avg_humidity": avg_humidity,
        "avg_wind_speed": avg_wind_speed,
        "avg_precipitation": avg_precipitation,
        "temp_trend": temp_trend,
        "humidity_trend": humidity_trend,
        "drought_index": drought_index,
        "data_points": len(historical_data),
    }


def calculate_wildfire_risk(current_weather, historical_patterns, region):
    """Calculate wildfire risk based on current weather, historical patterns, and region characteristics."""
    if not current_weather or not historical_patterns:
        return None

    # Base risk factors
    risk_score = 0
    factors = []

    # Temperature analysis
    temp_risk = 0
    if current_weather.temperature > 30:  # High temperature threshold
        temp_risk += 2
        factors.append("high temperature")
    elif current_weather.temperature > 25:
        temp_risk += 1
        factors.append("elevated temperature")

    # Compare with historical average
    if current_weather.temperature > historical_patterns["avg_temperature"] + 5:
        temp_risk += 1
        factors.append("temperature significantly above average")

    # Humidity analysis
    humidity_risk = 0
    if current_weather.humidity < 30:  # Low humidity threshold
        humidity_risk += 2
        factors.append("low humidity")
    elif current_weather.humidity < 40:
        humidity_risk += 1
        factors.append("reduced humidity")

    # Compare with historical average
    if current_weather.humidity < historical_patterns["avg_humidity"] - 10:
        humidity_risk += 1
        factors.append("humidity significantly below average")

    # Wind speed analysis
    wind_risk = 0
    if current_weather.wind_speed > 8:  # High wind threshold
        wind_risk += 2
        factors.append("strong winds")
    elif current_weather.wind_speed > 5:
        wind_risk += 1
        factors.append("moderate winds")

    # Precipitation analysis
    precip_risk = 0
    if current_weather.precipitation == 0:
        precip_risk += 1
        factors.append("no recent precipitation")
    if historical_patterns["avg_precipitation"] < 5:  # Low precipitation threshold
        precip_risk += 1
        factors.append("low average precipitation")

    # Historical trend analysis
    trend_risk = 0
    if historical_patterns["temp_trend"] > 0:  # Increasing temperature trend
        trend_risk += 1
        factors.append("rising temperature trend")
    if historical_patterns["humidity_trend"] < 0:  # Decreasing humidity trend
        trend_risk += 1
        factors.append("decreasing humidity trend")

    # Drought analysis
    drought_risk = 0
    if historical_patterns["drought_index"] > 2:  # Severe drought
        drought_risk += 2
        factors.append("severe drought conditions")
    elif historical_patterns["drought_index"] > 1:  # Moderate drought
        drought_risk += 1
        factors.append("moderate drought conditions")

    # Topographical risk (based on region elevation)
    topo_risk = 0
    if region.elevation > 2000:  # High elevation
        topo_risk += 1
        factors.append("high elevation terrain")
    elif region.elevation > 1000:  # Moderate elevation
        topo_risk += 0.5
        factors.append("moderate elevation terrain")

    # Calculate total risk score
    risk_score = (
        temp_risk
        + humidity_risk
        + wind_risk
        + precip_risk
        + trend_risk
        + drought_risk
        + topo_risk
    )

    # Determine risk level
    if risk_score >= 10:
        risk_level = WildfirePrediction.EXTREME
        risk_color = "danger"
    elif risk_score >= 7:
        risk_level = WildfirePrediction.HIGH
        risk_color = "warning"
    elif risk_score >= 4:
        risk_level = WildfirePrediction.MEDIUM
        risk_color = "info"
    else:
        risk_level = WildfirePrediction.LOW
        risk_color = "success"

    # Calculate confidence based on data points and factors considered
    confidence = min(
        0.95, 0.7 + (historical_patterns["data_points"] / 100) + (len(factors) * 0.05)
    )

    return {
        "risk_level": risk_level,
        "risk_color": risk_color,
        "confidence": confidence,
        "factors": factors,
    }


def generate_prediction_explanation(
    prediction, current_weather, historical_patterns, region
):
    """Generate a detailed explanation of the prediction."""
    if not prediction or not current_weather or not historical_patterns:
        return "Insufficient data for prediction"

    explanation_parts = []

    # Current conditions
    explanation_parts.append(
        f"Current conditions: Temperature {current_weather.temperature}°C, "
        f"Humidity {current_weather.humidity}%, "
        f"Wind Speed {current_weather.wind_speed} m/s"
    )

    # Historical context
    explanation_parts.append(
        f"Historical averages: Temperature {historical_patterns['avg_temperature']:.1f}°C, "
        f"Humidity {historical_patterns['avg_humidity']:.1f}%"
    )

    # Drought conditions
    if historical_patterns["drought_index"] > 1:
        explanation_parts.append(
            f"Drought index: {historical_patterns['drought_index']:.1f} "
            f"({'severe' if historical_patterns['drought_index'] > 2 else 'moderate'} drought)"
        )

    # Topographical context
    explanation_parts.append(f"Region elevation: {region.elevation}m")

    # Risk factors
    if prediction["factors"]:
        explanation_parts.append("Risk factors: " + ", ".join(prediction["factors"]))

    # Trend information
    if historical_patterns["temp_trend"] > 0:
        explanation_parts.append("Temperature has been trending upward")
    if historical_patterns["humidity_trend"] < 0:
        explanation_parts.append("Humidity has been trending downward")

    return ". ".join(explanation_parts)


class PredictionViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"])
    def predict_for_region(self, request):
        region_id = request.data.get("region_id")
        if not region_id:
            return Response(
                {"error": "Region ID is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            region = Region.objects.get(id=region_id)
        except Region.DoesNotExist:
            return Response(
                {"error": "Region not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Get current weather data
        current_weather = (
            WeatherData.objects.filter(region=region).order_by("-timestamp").first()
        )

        if not current_weather:
            return Response(
                {"error": "No weather data available for the region"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Analyze historical patterns
        historical_patterns = analyze_historical_patterns(region)
        if not historical_patterns:
            return Response(
                {"error": "Insufficient historical data for prediction"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Calculate risk
        risk_prediction = calculate_wildfire_risk(
            current_weather, historical_patterns, region
        )
        if not risk_prediction:
            return Response(
                {"error": "Could not calculate risk prediction"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Create prediction record
        prediction = WildfirePrediction.objects.create(
            region=region,
            prediction_date=timezone.now(),
            risk_level=risk_prediction["risk_level"],
            confidence=risk_prediction["confidence"],
            features_used={
                "current_weather": {
                    "temperature": current_weather.temperature,
                    "humidity": current_weather.humidity,
                    "wind_speed": current_weather.wind_speed,
                    "precipitation": current_weather.precipitation,
                },
                "historical_patterns": historical_patterns,
            },
            model_version="1.0",
        )

        return Response(
            {
                "prediction_id": prediction.id,
                "risk_level": prediction.get_risk_level_display(),
                "confidence": prediction.confidence,
                "explanation": generate_prediction_explanation(
                    risk_prediction, current_weather, historical_patterns, region
                ),
            }
        )

    def dashboard(self, request):
        regions = Region.objects.all()
        predictions = []

        for region in regions:
            try:
                # Get current weather data
                current_weather = (
                    WeatherData.objects.filter(region=region)
                    .order_by("-timestamp")
                    .first()
                )

                # If no recent weather data (within last hour) or no weather data at all
                if (
                    not current_weather
                    or (timezone.now() - current_weather.timestamp).total_seconds()
                    > 3600
                ):
                    try:
                        current_weather = fetch_current_weather(region)
                        if not current_weather:
                            raise Exception("Failed to fetch current weather data")
                    except Exception as e:
                        logger.error(
                            f"Error fetching weather data for region {region.id}: {e}"
                        )
                        predictions.append(
                            {
                                "region": region,
                                "prediction": None,
                                "risk_level": "No Data",
                                "risk_color": "secondary",
                                "confidence": "N/A",
                                "timestamp": "Weather data unavailable",
                                "explanation": f"Unable to fetch current weather data: {str(e)}",
                            }
                        )
                        continue

                # Analyze historical patterns
                historical_patterns = analyze_historical_patterns(region)
                if not historical_patterns:
                    predictions.append(
                        {
                            "region": region,
                            "prediction": None,
                            "risk_level": "No Data",
                            "risk_color": "secondary",
                            "confidence": "N/A",
                            "timestamp": "Insufficient historical data",
                            "explanation": "Not enough historical weather data available for prediction.",
                        }
                    )
                    continue

                # Calculate risk
                risk_prediction = calculate_wildfire_risk(
                    current_weather, historical_patterns, region
                )

                if not risk_prediction:
                    predictions.append(
                        {
                            "region": region,
                            "prediction": None,
                            "risk_level": "Error",
                            "risk_color": "secondary",
                            "confidence": "N/A",
                            "timestamp": "Error calculating risk",
                            "explanation": "An error occurred while calculating the risk prediction.",
                        }
                    )
                    continue

                # Create a new prediction record
                prediction = WildfirePrediction.objects.create(
                    region=region,
                    prediction_date=timezone.now(),
                    risk_level=risk_prediction["risk_level"],
                    confidence=risk_prediction["confidence"],
                    features_used={
                        "current_weather": {
                            "temperature": current_weather.temperature,
                            "humidity": current_weather.humidity,
                            "wind_speed": current_weather.wind_speed,
                            "precipitation": current_weather.precipitation,
                        },
                        "historical_patterns": historical_patterns,
                    },
                    model_version="1.0",
                )

                predictions.append(
                    {
                        "region": region,
                        "prediction": prediction,
                        "risk_level": prediction.get_risk_level_display(),
                        "risk_color": (
                            "success"
                            if prediction.risk_level == WildfirePrediction.LOW
                            else (
                                "warning"
                                if prediction.risk_level == WildfirePrediction.MEDIUM
                                else (
                                    "danger"
                                    if prediction.risk_level == WildfirePrediction.HIGH
                                    else "dark"
                                )
                            )
                        ),
                        "confidence": f"{prediction.confidence:.1%}",
                        "timestamp": prediction.prediction_date.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "explanation": generate_prediction_explanation(
                            risk_prediction,
                            current_weather,
                            historical_patterns,
                            region,
                        ),
                    }
                )

            except Exception as e:
                logger.error(f"Error fetching prediction for region {region.id}: {e}")
                predictions.append(
                    {
                        "region": region,
                        "prediction": None,
                        "risk_level": "Error",
                        "risk_color": "secondary",
                        "confidence": "N/A",
                        "timestamp": "Error loading prediction",
                        "explanation": f"An error occurred while generating the prediction: {str(e)}",
                    }
                )

        return render(
            request,
            "predictions/dashboard.html",
            {"predictions": predictions, "regions": regions},
        )


def generate_test_predictions():
    """Generate test predictions for all regions if none exist."""
    regions = Region.objects.all()
    for region in regions:
        if not WildfirePrediction.objects.filter(region=region).exists():
            # Generate a random risk level and confidence
            risk_level = random.choice(
                [
                    WildfirePrediction.LOW,
                    WildfirePrediction.MEDIUM,
                    WildfirePrediction.HIGH,
                    WildfirePrediction.EXTREME,
                ]
            )
            confidence = round(random.uniform(0.6, 0.95), 2)

            WildfirePrediction.objects.create(
                region=region,
                prediction_date=timezone.now(),
                risk_level=risk_level,
                confidence=confidence,
                features_used={"test": True},
                model_version="1.0.0",
            )


def dashboard(request):
    """Render the predictions dashboard with current predictions for all regions."""
    regions = Region.objects.all()
    predictions = []

    for region in regions:
        try:
            # Get current weather data
            current_weather = (
                WeatherData.objects.filter(region=region).order_by("-timestamp").first()
            )

            # If no recent weather data (within last hour) or no weather data at all
            if (
                not current_weather
                or (timezone.now() - current_weather.timestamp).total_seconds() > 3600
            ):
                try:
                    current_weather = fetch_current_weather(region)
                    if not current_weather:
                        raise Exception("Failed to fetch current weather data")
                except Exception as e:
                    logger.error(
                        f"Error fetching weather data for region {region.id}: {e}"
                    )
                    predictions.append(
                        {
                            "region": region,
                            "prediction": None,
                            "risk_level": "No Data",
                            "risk_color": "secondary",
                            "confidence": "N/A",
                            "timestamp": "Weather data unavailable",
                            "explanation": f"Unable to fetch current weather data: {str(e)}",
                        }
                    )
                    continue

            # Analyze historical patterns
            historical_patterns = analyze_historical_patterns(region)
            if not historical_patterns:
                predictions.append(
                    {
                        "region": region,
                        "prediction": None,
                        "risk_level": "No Data",
                        "risk_color": "secondary",
                        "confidence": "N/A",
                        "timestamp": "Insufficient historical data",
                        "explanation": "Not enough historical weather data available for prediction.",
                    }
                )
                continue

            # Calculate risk
            risk_prediction = calculate_wildfire_risk(
                current_weather, historical_patterns, region
            )

            if not risk_prediction:
                predictions.append(
                    {
                        "region": region,
                        "prediction": None,
                        "risk_level": "Error",
                        "risk_color": "secondary",
                        "confidence": "N/A",
                        "timestamp": "Error calculating risk",
                        "explanation": "An error occurred while calculating the risk prediction.",
                    }
                )
                continue

            # Create a new prediction record
            prediction = WildfirePrediction.objects.create(
                region=region,
                prediction_date=timezone.now(),
                risk_level=risk_prediction["risk_level"],
                confidence=risk_prediction["confidence"],
                features_used={
                    "current_weather": {
                        "temperature": current_weather.temperature,
                        "humidity": current_weather.humidity,
                        "wind_speed": current_weather.wind_speed,
                        "precipitation": current_weather.precipitation,
                    },
                    "historical_patterns": historical_patterns,
                },
                model_version="1.0",
            )

            predictions.append(
                {
                    "region": region,
                    "prediction": prediction,
                    "risk_level": prediction.get_risk_level_display(),
                    "risk_color": (
                        "success"
                        if prediction.risk_level == WildfirePrediction.LOW
                        else (
                            "warning"
                            if prediction.risk_level == WildfirePrediction.MEDIUM
                            else (
                                "danger"
                                if prediction.risk_level == WildfirePrediction.HIGH
                                else "dark"
                            )
                        )
                    ),
                    "confidence": f"{prediction.confidence:.1%}",
                    "timestamp": prediction.prediction_date.strftime("%Y-%m-%d %H:%M"),
                    "explanation": generate_prediction_explanation(
                        risk_prediction,
                        current_weather,
                        historical_patterns,
                        region,
                    ),
                }
            )

        except Exception as e:
            logger.error(f"Error fetching prediction for region {region.id}: {e}")
            predictions.append(
                {
                    "region": region,
                    "prediction": None,
                    "risk_level": "Error",
                    "risk_color": "secondary",
                    "confidence": "N/A",
                    "timestamp": "Error loading prediction",
                    "explanation": f"An error occurred while generating the prediction: {str(e)}",
                }
            )

    return render(
        request,
        "predictions/dashboard.html",
        {"predictions": predictions, "regions": regions},
    )
