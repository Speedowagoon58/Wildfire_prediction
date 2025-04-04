from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta, datetime
import random
import logging
from django.db.models import Avg

from .models import WildfirePrediction
from .serializers import WildfirePredictionSerializer
from .ml_model import WildfirePredictionModel
from apps.core.models import Region
from apps.weather.models import WeatherData
from apps.weather.services import fetch_current_weather
from .global_risk_factors import (
    calculate_soil_risk_factor,
    calculate_vegetation_risk_factor,
    calculate_climate_risk_multiplier,
)

logger = logging.getLogger(__name__)


def calculate_trend(data_points):
    """Calculate trend from historical data points."""
    if not data_points or len(data_points) < 2:
        return 0.0

    # Simple linear regression
    n = len(data_points)
    x = list(range(n))
    y = [float(point) for point in data_points]

    # Calculate means
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # Calculate slope
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    if denominator == 0:
        return 0.0

    slope = numerator / denominator
    return slope


# Instantiate the model (consider how this is managed in a production environment - singleton?)
# This will attempt to load the pre-trained model when the Django process starts.
# prediction_model = WildfirePredictionModel() # DEFER INSTANTIATION


def analyze_historical_patterns(region):
    """Analyze historical weather patterns for a region, considering seasonal variations."""
    try:
        # Get historical weather data for the past 30 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        historical_data = WeatherData.objects.filter(
            region=region, timestamp__range=(start_date, end_date)
        ).order_by("timestamp")

        if not historical_data:
            return None

        # Extract data points
        temperatures = [data.temperature for data in historical_data]
        humidity_values = [data.humidity for data in historical_data]
        wind_speeds = [data.wind_speed for data in historical_data]
        precipitation_values = [data.precipitation for data in historical_data]

        # Calculate trends
        temp_trend = calculate_trend(temperatures)
        humidity_trend = calculate_trend(humidity_values)
        wind_trend = calculate_trend(wind_speeds)
        precip_trend = calculate_trend(precipitation_values)

        # Calculate averages
        avg_temp = sum(temperatures) / len(temperatures) if temperatures else 0
        avg_humidity = (
            sum(humidity_values) / len(humidity_values) if humidity_values else 0
        )
        avg_wind = sum(wind_speeds) / len(wind_speeds) if wind_speeds else 0
        avg_precip = (
            sum(precipitation_values) / len(precipitation_values)
            if precipitation_values
            else 0
        )

        # Get current month for seasonal analysis
        current_month = timezone.now().month
        season = get_season(current_month)

        return {
            "temperature": {
                "average": round(avg_temp, 2),
                "trend": round(temp_trend, 4),
                "season": season,
            },
            "humidity": {
                "average": round(avg_humidity, 2),
                "trend": round(humidity_trend, 4),
            },
            "wind_speed": {
                "average": round(avg_wind, 2),
                "trend": round(wind_trend, 4),
            },
            "precipitation": {
                "average": round(avg_precip, 2),
                "trend": round(precip_trend, 4),
            },
        }

    except Exception as e:
        logger.error(f"Error analyzing historical patterns: {str(e)}")
        return None


def get_season(month):
    """Determine the season based on the month."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


def calculate_wildfire_risk(weather_data, region):
    """
    Calculate wildfire risk based on weather data, region characteristics, and global patterns
    """
    # Base risk factors
    temperature_risk = 0
    humidity_risk = 0
    wind_risk = 0
    precipitation_risk = 0

    # Temperature risk (higher risk with higher temperatures)
    if weather_data.temperature > 35:
        temperature_risk = 1.0
    elif weather_data.temperature > 30:
        temperature_risk = 0.8
    elif weather_data.temperature > 25:
        temperature_risk = 0.6
    elif weather_data.temperature > 20:
        temperature_risk = 0.4
    else:
        temperature_risk = 0.2

    # Humidity risk (higher risk with lower humidity)
    if weather_data.humidity < 30:
        humidity_risk = 1.0
    elif weather_data.humidity < 40:
        humidity_risk = 0.8
    elif weather_data.humidity < 50:
        humidity_risk = 0.6
    elif weather_data.humidity < 60:
        humidity_risk = 0.4
    else:
        humidity_risk = 0.2

    # Wind risk (higher risk with stronger winds)
    if weather_data.wind_speed > 30:
        wind_risk = 1.0
    elif weather_data.wind_speed > 20:
        wind_risk = 0.8
    elif weather_data.wind_speed > 10:
        wind_risk = 0.6
    elif weather_data.wind_speed > 5:
        wind_risk = 0.4
    else:
        wind_risk = 0.2

    # Precipitation risk (higher risk with less precipitation)
    if weather_data.precipitation == 0:
        precipitation_risk = 1.0
    elif weather_data.precipitation < 5:
        precipitation_risk = 0.8
    elif weather_data.precipitation < 10:
        precipitation_risk = 0.6
    elif weather_data.precipitation < 20:
        precipitation_risk = 0.4
    else:
        precipitation_risk = 0.2

    # Calculate base risk score (0-100)
    base_risk = (
        (temperature_risk * 0.3)
        + (humidity_risk * 0.25)
        + (wind_risk * 0.25)
        + (precipitation_risk * 0.2)
    ) * 100

    # Get current month for seasonal calculations
    current_month = datetime.now().month

    # Apply soil type factor using global patterns
    soil_factor = 1.0
    if region.soil_type:
        soil_factor = calculate_soil_risk_factor(
            region.soil_type,
            current_month,
            drought_index=getattr(weather_data, "drought_index", None),
        )

    # Apply vegetation density factor using global patterns
    vegetation_factor = calculate_vegetation_risk_factor(region.vegetation_density)

    # Apply climate zone factor
    climate_factor = calculate_climate_risk_multiplier(
        current_month, climate_zone=getattr(region, "climate_zone", "mediterranean")
    )

    # Calculate final risk score with all global factors
    final_risk = base_risk * soil_factor * vegetation_factor * climate_factor

    # Cap the risk score at 100
    final_risk = min(final_risk, 100)

    # Determine risk level with more granular thresholds
    if final_risk >= 80:
        risk_level = WildfirePrediction.EXTREME
    elif final_risk >= 60:
        risk_level = WildfirePrediction.HIGH
    elif final_risk >= 40:
        risk_level = WildfirePrediction.MEDIUM
    else:
        risk_level = WildfirePrediction.LOW

    return {
        "risk_score": round(final_risk, 2),
        "risk_level": risk_level,
        "factors": {
            "temperature": round(temperature_risk * 100, 2),
            "humidity": round(humidity_risk * 100, 2),
            "wind": round(wind_risk * 100, 2),
            "precipitation": round(precipitation_risk * 100, 2),
            "soil_type": round(soil_factor * 100, 2),
            "vegetation": round(vegetation_factor * 100, 2),
            "climate": round(climate_factor * 100, 2),
        },
        "confidence": 0.85,  # Updated confidence with global factors
    }


def generate_prediction_explanation(
    prediction, current_weather, historical_patterns, region
):
    """Generate a detailed explanation of the prediction."""
    if not prediction or not current_weather or not historical_patterns:
        return "Insufficient data for prediction"

    # Helper function to get weather attribute
    def get_weather_value(weather, attr):
        if hasattr(weather, attr):
            return getattr(weather, attr)
        return weather[attr]

    explanation_parts = []

    # Current conditions
    explanation_parts.append(
        f"Current conditions: Temperature {get_weather_value(current_weather, 'temperature')}°C, "
        f"Humidity {get_weather_value(current_weather, 'humidity')}%, "
        f"Wind Speed {get_weather_value(current_weather, 'wind_speed')} m/s"
    )

    # Historical context
    explanation_parts.append(
        f"Historical averages: Temperature {historical_patterns['temperature']['average']:.1f}°C, "
        f"Humidity {historical_patterns['humidity']['average']:.1f}%"
    )

    # Drought conditions
    if historical_patterns["temperature"]["trend"] > 0:
        explanation_parts.append("Temperature has been trending upward")
    if historical_patterns["humidity"]["trend"] < 0:
        explanation_parts.append("Humidity has been trending downward")

    # Topographical context
    explanation_parts.append(f"Region elevation: {region.elevation}m")

    # Risk factors
    if prediction["factors"]:
        explanation_parts.append("Risk factors: " + ", ".join(prediction["factors"]))

    # Trend information
    if historical_patterns["temperature"]["trend"] > 0:
        explanation_parts.append("Temperature has been trending upward")
    if historical_patterns["humidity"]["trend"] < 0:
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
        risk_prediction = calculate_wildfire_risk(current_weather, region)
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
                risk_prediction = calculate_wildfire_risk(current_weather, region)

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
                            "temperature": (
                                current_weather.temperature
                                if hasattr(current_weather, "temperature")
                                else current_weather["temperature"]
                            ),
                            "humidity": (
                                current_weather.humidity
                                if hasattr(current_weather, "humidity")
                                else current_weather["humidity"]
                            ),
                            "wind_speed": (
                                current_weather.wind_speed
                                if hasattr(current_weather, "wind_speed")
                                else current_weather["wind_speed"]
                            ),
                            "precipitation": (
                                current_weather.precipitation
                                if hasattr(current_weather, "precipitation")
                                else current_weather["precipitation"]
                            ),
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
            risk_prediction = calculate_wildfire_risk(current_weather, region)

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
                        "temperature": (
                            current_weather.temperature
                            if hasattr(current_weather, "temperature")
                            else current_weather["temperature"]
                        ),
                        "humidity": (
                            current_weather.humidity
                            if hasattr(current_weather, "humidity")
                            else current_weather["humidity"]
                        ),
                        "wind_speed": (
                            current_weather.wind_speed
                            if hasattr(current_weather, "wind_speed")
                            else current_weather["wind_speed"]
                        ),
                        "precipitation": (
                            current_weather.precipitation
                            if hasattr(current_weather, "precipitation")
                            else current_weather["precipitation"]
                        ),
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
