from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from datetime import timedelta, datetime
import random
import logging
from django.db.models import Avg, Max, Min, Count
import numpy as np
from scipy import stats
import json
from django.contrib.auth.decorators import login_required

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
from apps.core.serializers import RegionSerializer
from .utils import analyze_historical_patterns, get_risk_color

logger = logging.getLogger(__name__)


def calculate_trend(data_points, window_size=7):
    """
    Calculate trend metrics for a series of data points.

    Args:
        data_points: List of numerical values
        window_size: Window size for moving average

    Returns:
        Dictionary containing trend metrics
    """
    try:
        if not data_points or len(data_points) < 2:
            return {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": [],
                "volatility": 0,
                "seasonality": 0,
            }

        # Convert to numpy array
        data = np.array(data_points)

        # Calculate linear trend
        x = np.arange(len(data))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, data)

        # Calculate moving average
        moving_avg = []
        if len(data) >= window_size:
            moving_avg = np.convolve(
                data, np.ones(window_size) / window_size, mode="valid"
            )

        # Calculate volatility (standard deviation)
        volatility = np.std(data)

        # Calculate basic seasonality (correlation with shifted series)
        if len(data) > window_size:
            shifted = np.roll(data, window_size)
            # Ensure we're working with 1D arrays
            data_slice = data[window_size:]
            shifted_slice = shifted[window_size:]

            # Calculate correlation coefficient safely
            if len(data_slice) > 1 and len(shifted_slice) > 1:
                try:
                    # Reshape arrays to 2D for correlation
                    data_2d = data_slice.reshape(-1, 1)
                    shifted_2d = shifted_slice.reshape(-1, 1)
                    corr_matrix = np.corrcoef(data_2d.T, shifted_2d.T)
                    seasonality = (
                        float(corr_matrix[0, 1]) if corr_matrix.shape == (2, 2) else 0
                    )
                except Exception as e:
                    logger.error(f"Error calculating correlation: {str(e)}")
                    seasonality = 0
            else:
                seasonality = 0
        else:
            seasonality = 0

        return {
            "linear_trend": float(slope),
            "r_squared": float(r_value**2),
            "moving_average": (
                [float(x) for x in moving_avg.tolist()] if len(moving_avg) > 0 else []
            ),
            "volatility": float(volatility),
            "seasonality": float(seasonality),
        }

    except Exception as e:
        logger.error(f"Error calculating trend: {str(e)}")
        return {
            "linear_trend": 0,
            "r_squared": 0,
            "moving_average": [],
            "volatility": 0,
            "seasonality": 0,
        }


# Instantiate the model (consider how this is managed in a production environment - singleton?)
# This will attempt to load the pre-trained model when the Django process starts.
# prediction_model = WildfirePredictionModel() # DEFER INSTANTIATION


def analyze_historical_patterns(region):
    """Analyze historical weather patterns for a region with enhanced metrics."""
    try:
        # Get historical weather data for the past 90 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)

        historical_data = WeatherData.objects.filter(
            region=region, timestamp__range=(start_date, end_date)
        ).order_by("timestamp")

        if not historical_data:
            logger.warning(f"No historical data found for region {region.name}")
            return None

        # Extract data points
        temperatures = [data.temperature for data in historical_data]
        humidity_values = [data.humidity for data in historical_data]
        wind_speeds = [data.wind_speed for data in historical_data]
        precipitation_values = [data.precipitation for data in historical_data]

        # Calculate enhanced trends with error handling
        try:
            temp_trends = calculate_trend(temperatures)
            humidity_trends = calculate_trend(humidity_values)
            wind_trends = calculate_trend(wind_speeds)
            precip_trends = calculate_trend(precipitation_values)
        except Exception as e:
            logger.error(f"Error calculating trends: {str(e)}")
            temp_trends = humidity_trends = wind_trends = precip_trends = {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": [],
                "volatility": 0,
                "seasonality": 0,
            }

        # Calculate statistical measures with error handling
        try:
            temp_stats = {
                "mean": np.mean(temperatures) if temperatures else 0,
                "std": np.std(temperatures) if temperatures else 0,
                "max": max(temperatures) if temperatures else 0,
                "min": min(temperatures) if temperatures else 0,
                "range": (max(temperatures) - min(temperatures)) if temperatures else 0,
            }

            humidity_stats = {
                "mean": np.mean(humidity_values) if humidity_values else 0,
                "std": np.std(humidity_values) if humidity_values else 0,
                "max": max(humidity_values) if humidity_values else 0,
                "min": min(humidity_values) if humidity_values else 0,
                "range": (
                    (max(humidity_values) - min(humidity_values))
                    if humidity_values
                    else 0
                ),
            }

            wind_stats = {
                "mean": np.mean(wind_speeds) if wind_speeds else 0,
                "std": np.std(wind_speeds) if wind_speeds else 0,
                "max": max(wind_speeds) if wind_speeds else 0,
                "min": min(wind_speeds) if wind_speeds else 0,
                "range": (max(wind_speeds) - min(wind_speeds)) if wind_speeds else 0,
            }

            precip_stats = {
                "mean": np.mean(precipitation_values) if precipitation_values else 0,
                "std": np.std(precipitation_values) if precipitation_values else 0,
                "max": max(precipitation_values) if precipitation_values else 0,
                "min": min(precipitation_values) if precipitation_values else 0,
                "range": (
                    (max(precipitation_values) - min(precipitation_values))
                    if precipitation_values
                    else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            temp_stats = humidity_stats = wind_stats = precip_stats = {
                "mean": 0,
                "std": 0,
                "max": 0,
                "min": 0,
                "range": 0,
            }

        # Get current month for seasonal analysis
        current_month = timezone.now().month
        season = get_season(current_month)

        # Calculate extreme weather events with error handling
        try:
            extreme_events = {
                "high_temp_days": (
                    sum(1 for t in temperatures if t > 35) if temperatures else 0
                ),
                "low_humidity_days": (
                    sum(1 for h in humidity_values if h < 30) if humidity_values else 0
                ),
                "high_wind_days": (
                    sum(1 for w in wind_speeds if w > 20) if wind_speeds else 0
                ),
                "drought_days": (
                    sum(1 for p in precipitation_values if p < 1)
                    if precipitation_values
                    else 0
                ),
            }
        except Exception as e:
            logger.error(f"Error calculating extreme events: {str(e)}")
            extreme_events = {
                "high_temp_days": 0,
                "low_humidity_days": 0,
                "high_wind_days": 0,
                "drought_days": 0,
            }

        return {
            "temperature": {
                "stats": temp_stats,
                "trends": temp_trends,
                "season": season,
                "extreme_events": extreme_events["high_temp_days"],
            },
            "humidity": {
                "stats": humidity_stats,
                "trends": humidity_trends,
                "extreme_events": extreme_events["low_humidity_days"],
            },
            "wind_speed": {
                "stats": wind_stats,
                "trends": wind_trends,
                "extreme_events": extreme_events["high_wind_days"],
            },
            "precipitation": {
                "stats": precip_stats,
                "trends": precip_trends,
                "extreme_events": extreme_events["drought_days"],
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


def calculate_wildfire_risk(weather_data, historical_data=None):
    """Calculate wildfire risk based on weather data and historical patterns."""
    try:
        # Initialize risk factors
        risk_factors = {
            "temperature_risk": 0,
            "humidity_risk": 0,
            "wind_risk": 0,
            "precipitation_risk": 0,
            "historical_risk": 0,
            "environmental_risk": 0,
        }

        # Calculate temperature risk (adjusted for Moroccan climate)
        temp = float(getattr(weather_data, "temperature", 0))
        if temp > 35:  # Very hot
            risk_factors["temperature_risk"] = 1.0
        elif temp > 30:  # Hot
            risk_factors["temperature_risk"] = 0.8
        elif temp > 25:  # Warm
            risk_factors["temperature_risk"] = 0.6
        elif temp > 20:  # Mild
            risk_factors["temperature_risk"] = 0.4
        else:  # Cool
            risk_factors["temperature_risk"] = 0.2

        # Calculate humidity risk
        humidity = float(getattr(weather_data, "humidity", 0))
        if humidity < 20:  # Very dry
            risk_factors["humidity_risk"] = 1.0
        elif humidity < 30:  # Dry
            risk_factors["humidity_risk"] = 0.8
        elif humidity < 40:  # Moderate
            risk_factors["humidity_risk"] = 0.6
        elif humidity < 50:  # Humid
            risk_factors["humidity_risk"] = 0.4
        else:  # Very humid
            risk_factors["humidity_risk"] = 0.2

        # Calculate wind risk
        wind_speed = float(getattr(weather_data, "wind_speed", 0))
        if wind_speed > 40:  # Very strong winds
            risk_factors["wind_risk"] = 1.0
        elif wind_speed > 30:  # Strong winds
            risk_factors["wind_risk"] = 0.8
        elif wind_speed > 20:  # Moderate winds
            risk_factors["wind_risk"] = 0.6
        elif wind_speed > 10:  # Light winds
            risk_factors["wind_risk"] = 0.4
        else:  # Very light winds
            risk_factors["wind_risk"] = 0.2

        # Calculate precipitation risk
        precipitation = float(getattr(weather_data, "precipitation", 0))
        if precipitation == 0 and temp > 30:  # No rain and hot
            risk_factors["precipitation_risk"] = 1.0
        elif precipitation == 0:  # No rain but cooler
            risk_factors["precipitation_risk"] = 0.8
        elif precipitation < 2:  # Very light rain
            risk_factors["precipitation_risk"] = 0.6
        elif precipitation < 5:  # Light rain
            risk_factors["precipitation_risk"] = 0.4
        else:  # Significant rain
            risk_factors["precipitation_risk"] = 0.2

        # Calculate historical risk if data is available
        if historical_data:
            risk_factors["historical_risk"] = float(
                calculate_historical_risk(historical_data)
            )
        else:
            risk_factors["historical_risk"] = 0.5  # Default moderate risk

        # Calculate environmental risk with adjusted weights
        risk_factors["environmental_risk"] = float(
            risk_factors["temperature_risk"] * 0.25  # Temperature is important
            + risk_factors["humidity_risk"] * 0.25  # Humidity is equally important
            + risk_factors["wind_risk"] * 0.2  # Wind has significant impact
            + risk_factors["precipitation_risk"] * 0.2  # Precipitation is important
            + risk_factors["historical_risk"]
            * 0.1  # Historical patterns have some influence
        )

        # Determine risk level based on environmental risk score
        if risk_factors["environmental_risk"] >= 0.7:  # High risk threshold
            risk_level = WildfirePrediction.HIGH_RISK
        elif risk_factors["environmental_risk"] >= 0.5:  # Medium risk threshold
            risk_level = WildfirePrediction.MEDIUM_RISK
        else:
            risk_level = WildfirePrediction.LOW_RISK

        # Calculate confidence based on the strength of the risk factors
        confidence = min(100, max(50, int(risk_factors["environmental_risk"] * 100)))

        # Ensure all values are JSON serializable
        features_used = {
            "current_weather": {
                "temperature": float(temp),
                "humidity": float(humidity),
                "wind_speed": float(wind_speed),
                "precipitation": float(precipitation),
            },
            "risk_factors": {k: float(v) for k, v in risk_factors.items()},
        }

        return {
            "risk_level": risk_level,
            "confidence": confidence,
            "features_used": features_used,
        }

    except Exception as e:
        logger.error(f"Error calculating wildfire risk: {str(e)}")
        return None


def get_risk_color(risk_level):
    """Get the Bootstrap color class for a risk level."""
    color_map = {
        WildfirePrediction.LOW_RISK: "success",
        WildfirePrediction.MEDIUM_RISK: "warning",
        WildfirePrediction.HIGH_RISK: "danger",
    }
    return color_map.get(risk_level, "secondary")


def calculate_historical_risk(historical_data):
    """Calculate historical risk based on past wildfire patterns."""
    try:
        if not historical_data:
            return 0.5  # Default moderate risk if no historical data

        # Extract temperature data from historical data
        temperature_data = historical_data.get("temperature", {})
        if not temperature_data:
            return 0.5

        # Get trend data
        temp_trends = temperature_data.get("trends", {})
        if not temp_trends:
            return 0.5

        # Calculate risk based on trend metrics
        linear_trend = temp_trends.get("linear_trend", 0)
        r_squared = temp_trends.get("r_squared", 0)
        volatility = temp_trends.get("volatility", 0)
        seasonality = temp_trends.get("seasonality", 0)

        # Weight the different trend factors
        trend_score = (
            abs(linear_trend) * 0.4  # Linear trend (positive or negative)
            + r_squared * 0.3  # How well the trend fits
            + min(volatility, 1.0) * 0.2  # Volatility (capped at 1.0)
            + abs(seasonality) * 0.1  # Seasonal patterns
        )

        # Normalize trend score to 0-1 range
        normalized_score = min(max(trend_score, 0), 1)

        # Map to risk levels
        if normalized_score > 0.7:
            return 0.8  # High historical risk
        elif normalized_score > 0.4:
            return 0.6  # Moderate historical risk
        elif normalized_score > 0.2:
            return 0.4  # Slightly elevated historical risk
        else:
            return 0.2  # Low historical risk

    except Exception as e:
        logger.error(f"Error calculating historical risk: {str(e)}")
        return 0.5  # Default to moderate risk on error


def generate_prediction_explanation(prediction):
    """Generate a human-readable explanation for a wildfire prediction."""
    try:
        # Get current weather data from features_used
        features = prediction.features_used
        if isinstance(features, str):
            features = json.loads(features)

        current_weather = features.get("current_weather", {})
        temperature = current_weather.get("temperature", 0)
        humidity = current_weather.get("humidity", 0)
        wind_speed = current_weather.get("wind_speed", 0)
        precipitation = current_weather.get("precipitation", 0)

        # Get region-specific information
        region = prediction.region
        region_name = region.name
        region_type = getattr(region, "type", "region")
        soil_type = str(getattr(region, "soil_type", "Unknown"))
        vegetation_density = getattr(region, "vegetation_density", "moderate")
        climate_zone = getattr(region, "climate_zone", "temperate")

        # Create region-specific context
        region_context = f"In {region_name}, a {region_type} area with {soil_type.lower()} soil and {vegetation_density} vegetation density, "

        # Build detailed weather conditions explanation
        weather_conditions = []

        # Temperature explanation with actual value and seasonal context
        season = get_current_season()
        if temperature > 30:
            weather_conditions.append(
                f"temperatures are significantly high at {temperature}°C, which is {'typical' if season in ['summer'] else 'unusual'} for this {season}"
            )
        elif temperature > 25:
            weather_conditions.append(
                f"temperatures are elevated at {temperature}°C, which is {'normal' if season in ['summer', 'spring'] else 'above average'} for this {season}"
            )
        elif temperature > 20:
            weather_conditions.append(
                f"temperatures are moderate at {temperature}°C, which is {'typical' if season in ['spring', 'summer', 'autumn'] else 'unusual'} for this {season}"
            )
        else:
            weather_conditions.append(
                f"temperatures are cool at {temperature}°C, which is {'normal' if season in ['winter', 'autumn'] else 'below average'} for this {season}"
            )

        # Humidity explanation with actual value and soil type context
        if humidity < 30:
            weather_conditions.append(
                f"humidity is critically low at {humidity}%, which is particularly concerning given the {soil_type.lower()} soil's {'poor' if soil_type == 'Sandy' else 'moderate'} moisture retention"
            )
        elif humidity < 40:
            weather_conditions.append(
                f"humidity is low at {humidity}%, contributing to dry conditions that are {'especially risky' if soil_type == 'Sandy' else 'moderately concerning'} for this soil type"
            )
        elif humidity < 60:
            weather_conditions.append(
                f"humidity is moderate at {humidity}%, providing {'some' if soil_type == 'Clay' else 'adequate'} moisture retention for the {soil_type.lower()} soil"
            )
        else:
            weather_conditions.append(
                f"humidity is high at {humidity}%, helping maintain moisture in the {soil_type.lower()} soil and vegetation"
            )

        # Wind explanation with actual value and vegetation context
        if wind_speed > 30:
            weather_conditions.append(
                f"strong winds at {wind_speed} km/h, particularly significant in areas with {vegetation_density} vegetation"
            )
        elif wind_speed > 20:
            weather_conditions.append(
                f"moderate to strong winds at {wind_speed} km/h, with {'increased' if vegetation_density == 'dense' else 'moderate'} impact due to {vegetation_density} vegetation"
            )
        elif wind_speed > 10:
            weather_conditions.append(
                f"moderate winds at {wind_speed} km/h in the {vegetation_density} vegetation"
            )
        else:
            weather_conditions.append(
                f"calm winds at {wind_speed} km/h, though {'dense' if vegetation_density == 'dense' else 'moderate'} vegetation present"
            )

        # Precipitation explanation with actual value and climate zone context
        if precipitation < 5:
            weather_conditions.append(
                f"minimal precipitation of {precipitation}mm, which is {'particularly concerning' if climate_zone in ['mediterranean', 'semi_arid'] else 'concerning'} for this {climate_zone} climate zone"
            )
        elif precipitation < 10:
            weather_conditions.append(
                f"low precipitation of {precipitation}mm, which is {'typical' if climate_zone == 'semi_arid' else 'below average'} for this {climate_zone} region"
            )
        elif precipitation < 20:
            weather_conditions.append(
                f"moderate precipitation of {precipitation}mm, which is {'adequate' if climate_zone == 'temperate' else 'below normal'} for this {climate_zone} climate"
            )
        else:
            weather_conditions.append(
                f"significant precipitation of {precipitation}mm, which is {'beneficial' if climate_zone in ['mediterranean', 'semi_arid'] else 'normal'} for this {climate_zone} region"
            )

        # Get historical patterns
        historical_patterns = features.get("historical_patterns", {})
        if historical_patterns:
            trend = historical_patterns.get("trend", 0)
            if trend > 0.7:
                historical_context = (
                    " Historical data shows a strong increasing trend in conditions."
                )
            elif trend > 0.4:
                historical_context = " Historical patterns indicate a moderate increase in conditions over time."
            elif trend > 0.2:
                historical_context = (
                    " Historical data suggests a slight increase in patterns."
                )
            else:
                historical_context = (
                    " Historical data shows generally stable or decreasing patterns."
                )
        else:
            historical_context = ""

        # Combine all explanations
        weather_text = ". ".join(weather_conditions)
        explanation = f"{region_context}{weather_text}.{historical_context}"

        return explanation

    except Exception as e:
        logger.error(f"Error generating prediction explanation: {str(e)}")
        return f"Unable to generate detailed explanation for {prediction.region.name}."


def get_current_season():
    """Helper function to determine the current season."""
    month = timezone.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


class PredictionViewSet(viewsets.ModelViewSet):
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
        risk_prediction = calculate_wildfire_risk(current_weather, historical_patterns)
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
            features_used=risk_prediction["features_used"],
            model_version="1.0",
        )

        return Response(
            {
                "prediction_id": prediction.id,
                "risk_level": prediction.get_risk_level_display(),
                "confidence": prediction.confidence,
                "explanation": generate_prediction_explanation(prediction),
            }
        )

    def list(self, request, *args, **kwargs):
        try:
            # Get all regions
            regions = Region.objects.all()
            predictions = []

            for region in regions:
                # Get current weather data
                current_weather = fetch_current_weather(region)

                # Get historical patterns
                historical_patterns = analyze_historical_patterns(region)

                # Calculate risk
                risk_prediction = calculate_wildfire_risk(
                    current_weather, historical_patterns
                )

                if not risk_prediction:
                    continue

                # Create a WildfirePrediction object for explanation
                prediction_obj = WildfirePrediction(
                    region=region,
                    risk_level=risk_prediction["risk_level"],
                    confidence=risk_prediction["confidence"],
                    risk_factors=risk_prediction.get("risk_factors", {}),
                )

                predictions.append(
                    {
                        "region": RegionSerializer(region).data,
                        "risk_level": risk_prediction["risk_level"],
                        "confidence": risk_prediction["confidence"],
                        "risk_color": get_risk_color(risk_prediction["risk_level"]),
                        "explanation": generate_prediction_explanation(prediction_obj),
                        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                )

            return Response(predictions)
        except Exception as e:
            logger.error(f"Error in prediction list: {str(e)}")
            return Response(
                {"error": "Failed to generate predictions"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @login_required
    def dashboard(self, request):
        """Display wildfire predictions dashboard."""
        try:
            # Get all regions
            regions = Region.objects.all()
            predictions = []

            for region in regions:
                try:
                    # Get current weather data
                    current_weather = fetch_current_weather(region)
                    if not current_weather:
                        logger.warning(
                            f"No current weather data for region {region.name}"
                        )
                        continue

                    # Analyze historical patterns
                    historical_patterns = analyze_historical_patterns(region)
                    if not historical_patterns:
                        logger.warning(
                            f"No historical patterns available for region {region.name}"
                        )
                        continue

                    # Calculate wildfire risk
                    risk_prediction = calculate_wildfire_risk(
                        current_weather, historical_patterns
                    )
                    if not risk_prediction:
                        logger.warning(
                            f"Could not calculate risk for region {region.name}"
                        )
                        continue

                    # Create prediction record
                    prediction = WildfirePrediction.objects.create(
                        region=region,
                        prediction_date=timezone.now(),
                        risk_level=risk_prediction["risk_level"].lower(),
                        confidence=risk_prediction["confidence"],
                        features_used=risk_prediction["features_used"],
                        model_version="1.0",
                    )

                    # Generate explanation
                    explanation = generate_prediction_explanation(prediction)

                    # Get major forests for the region
                    major_forests = region.forests.all().order_by("-area")[
                        :3
                    ]  # Get top 3 largest forests

                    predictions.append(
                        {
                            "region": region,
                            "prediction": prediction,
                            "risk_level": prediction.risk_level,  # Raw value for map
                            "risk_level_display": prediction.get_risk_level_display(),  # Display value for cards
                            "risk_color": get_risk_color(prediction.risk_level),
                            "confidence": f"{prediction.confidence:.1%}",
                            "timestamp": prediction.prediction_date.strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "explanation": generate_prediction_explanation(prediction),
                            "major_forests": [forest.name for forest in major_forests],
                        }
                    )

                except Exception as e:
                    logger.error(
                        f"Error fetching prediction for region {region.id}: {str(e)}"
                    )
                    continue

            return render(
                request, "predictions/dashboard.html", {"predictions": predictions}
            )

        except Exception as e:
            logger.error(f"Error in dashboard view: {str(e)}")
            return render(
                request,
                "predictions/dashboard.html",
                {
                    "predictions": [],
                    "error": "An error occurred while fetching predictions. Please try again later.",
                },
            )


def generate_test_predictions():
    """Generate test predictions for all regions if none exist."""
    regions = Region.objects.all()
    for region in regions:
        if not WildfirePrediction.objects.filter(region=region).exists():
            # Generate a random risk level and confidence
            risk_level = random.choice(
                [
                    WildfirePrediction.LOW_RISK,
                    WildfirePrediction.MEDIUM_RISK,
                    WildfirePrediction.HIGH_RISK,
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


def generate_test_weather_data():
    """Generate test weather data for regions that don't have any."""
    regions = Region.objects.all()
    now = timezone.now()

    for region in regions:
        # Check if region has any weather data
        if not WeatherData.objects.filter(region=region).exists():
            logger.info(f"Generating test weather data for region: {region.name}")

            # Generate test data for the past 7 days
            for i in range(7):
                timestamp = now - timedelta(days=i)

                # Create weather data with realistic values
                WeatherData.objects.create(
                    region=region,
                    timestamp=timestamp,
                    temperature=random.uniform(15, 35),  # 15-35°C
                    humidity=random.uniform(30, 80),  # 30-80%
                    wind_speed=random.uniform(0, 15),  # 0-15 m/s
                    wind_direction=random.uniform(0, 360),  # 0-360 degrees
                    precipitation=random.uniform(0, 10),  # 0-10 mm
                    pressure=random.uniform(980, 1020),  # 980-1020 hPa
                )

            logger.info(f"Generated test weather data for region: {region.name}")
        else:
            logger.info(f"Region {region.name} already has weather data")


def dashboard(request):
    """Render the predictions dashboard with current predictions for all regions."""
    # Generate test weather data if needed
    generate_test_weather_data()

    regions = Region.objects.all()
    logger.info(f"Found {regions.count()} regions")

    predictions = []

    for region in regions:
        try:
            logger.info(f"Processing region: {region.name}")

            # Get current weather data
            current_weather = (
                WeatherData.objects.filter(region=region).order_by("-timestamp").first()
            )

            if current_weather:
                logger.info(
                    f"Found weather data for {region.name}: temp={current_weather.temperature}, humidity={current_weather.humidity}"
                )
            else:
                logger.warning(f"No weather data found for region {region.name}")

            # If no recent weather data (within last hour) or no weather data at all
            if (
                not current_weather
                or (timezone.now() - current_weather.timestamp).total_seconds() > 3600
            ):
                logger.warning(f"No recent weather data for region {region.name}")
                predictions.append(
                    {
                        "region": region,
                        "prediction": None,
                        "risk_level": "No Data",
                        "risk_color": "secondary",
                        "confidence": "N/A",
                        "timestamp": "No recent weather data",
                        "explanation": "No recent weather data available for prediction.",
                    }
                )
                continue

            # Get historical patterns
            historical_patterns = analyze_historical_patterns(region)
            if not historical_patterns:
                logger.warning(f"No historical patterns for region {region.name}")
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

            logger.info(f"Found historical patterns for region {region.name}")

            # Calculate risk
            risk_prediction = calculate_wildfire_risk(
                current_weather, historical_patterns
            )

            if not risk_prediction:
                logger.error(f"Failed to calculate risk for region {region.name}")
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

            logger.info(
                f"Calculated risk for region {region.name}: {risk_prediction['risk_level']}"
            )

            # Create prediction record
            prediction = WildfirePrediction.objects.create(
                region=region,
                prediction_date=timezone.now(),
                risk_level=risk_prediction["risk_level"].lower(),
                confidence=risk_prediction["confidence"],
                features_used=risk_prediction["features_used"],
                model_version="1.0",
            )

            logger.info(f"Created prediction record for region {region.name}")

            # Get major forests for the region
            major_forests = region.forests.all().order_by("-area")[
                :3
            ]  # Get top 3 largest forests

            predictions.append(
                {
                    "region": region,
                    "prediction": prediction,
                    "risk_level": prediction.risk_level,  # Raw value for map
                    "risk_level_display": prediction.get_risk_level_display(),  # Display value for cards
                    "risk_color": get_risk_color(prediction.risk_level),
                    "confidence": f"{prediction.confidence:.1%}",
                    "timestamp": prediction.prediction_date.strftime("%Y-%m-%d %H:%M"),
                    "explanation": generate_prediction_explanation(prediction),
                    "major_forests": [forest.name for forest in major_forests],
                }
            )

            logger.info(f"Added prediction to list for region {region.name}")

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

    # For debugging - log the predictions
    logger.info(f"Number of predictions: {len(predictions)}")
    for pred in predictions:
        logger.info(
            f"Region: {pred['region'].name}, Risk Level: {pred.get('risk_level', 'N/A')}"
        )

    return render(
        request,
        "predictions/dashboard.html",
        {
            "regions": predictions,  # Pass predictions as regions for the template
        },
    )
