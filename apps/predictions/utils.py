import logging
from django.utils import timezone
from datetime import timedelta
import numpy as np
from scipy import stats
from apps.weather.models import WeatherData
from .models import WildfirePrediction

logger = logging.getLogger(__name__)


def analyze_historical_patterns(region):
    """Analyze historical weather patterns for a region."""
    try:
        # Get all available historical data, up to 90 days
        end_date = timezone.now()
        start_date = end_date - timedelta(days=90)

        historical_data = WeatherData.objects.filter(
            region=region, timestamp__range=(start_date, end_date)
        ).order_by("timestamp")

        if not historical_data:
            logger.warning(f"No historical data found for region {region.name}")
            # Try to get at least the current weather data
            current_data = (
                WeatherData.objects.filter(region=region).order_by("-timestamp").first()
            )

            if current_data:
                logger.info(f"Found current weather data for {region.name}")
                historical_data = [current_data]
            else:
                logger.error(f"No weather data at all for region {region.name}")
                return None

        # Log the amount of data we're working with
        logger.info(
            f"Analyzing {len(historical_data)} weather records for {region.name}"
        )

        # Extract data points
        temperatures = [data.temperature for data in historical_data]
        humidity_values = [data.humidity for data in historical_data]
        wind_speeds = [data.wind_speed for data in historical_data]
        precipitation_values = [data.precipitation for data in historical_data]

        # Calculate trends if we have enough data points
        if len(historical_data) > 1:
            temp_trends = calculate_trend(temperatures)
            humidity_trends = calculate_trend(humidity_values)
            wind_trends = calculate_trend(wind_speeds)
            precip_trends = calculate_trend(precipitation_values)
        else:
            # Use simplified trends for single data point
            temp_trends = {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": temperatures,
                "volatility": 0,
                "seasonality": 0,
            }
            humidity_trends = {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": humidity_values,
                "volatility": 0,
                "seasonality": 0,
            }
            wind_trends = {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": wind_speeds,
                "volatility": 0,
                "seasonality": 0,
            }
            precip_trends = {
                "linear_trend": 0,
                "r_squared": 0,
                "moving_average": precipitation_values,
                "volatility": 0,
                "seasonality": 0,
            }

        # Calculate statistical measures
        temp_stats = {
            "mean": np.mean(temperatures) if temperatures else 0,
            "std": np.std(temperatures) if len(temperatures) > 1 else 0,
            "max": max(temperatures) if temperatures else 0,
            "min": min(temperatures) if temperatures else 0,
            "range": max(temperatures) - min(temperatures) if temperatures else 0,
        }

        humidity_stats = {
            "mean": np.mean(humidity_values) if humidity_values else 0,
            "std": np.std(humidity_values) if len(humidity_values) > 1 else 0,
            "max": max(humidity_values) if humidity_values else 0,
            "min": min(humidity_values) if humidity_values else 0,
            "range": (
                max(humidity_values) - min(humidity_values) if humidity_values else 0
            ),
        }

        wind_stats = {
            "mean": np.mean(wind_speeds) if wind_speeds else 0,
            "std": np.std(wind_speeds) if len(wind_speeds) > 1 else 0,
            "max": max(wind_speeds) if wind_speeds else 0,
            "min": min(wind_speeds) if wind_speeds else 0,
            "range": max(wind_speeds) - min(wind_speeds) if wind_speeds else 0,
        }

        precip_stats = {
            "mean": np.mean(precipitation_values) if precipitation_values else 0,
            "std": np.std(precipitation_values) if len(precipitation_values) > 1 else 0,
            "max": max(precipitation_values) if precipitation_values else 0,
            "min": min(precipitation_values) if precipitation_values else 0,
            "range": (
                max(precipitation_values) - min(precipitation_values)
                if precipitation_values
                else 0
            ),
        }

        # Get current month for seasonal analysis
        current_month = timezone.now().month
        season = get_season(current_month)

        # Calculate extreme weather events
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
        logger.error(f"Error analyzing historical patterns for {region.name}: {str(e)}")
        return None


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


def get_risk_color(risk_level):
    """Get the Bootstrap color class for a risk level."""
    color_map = {
        WildfirePrediction.LOW_RISK: "success",
        WildfirePrediction.MEDIUM_RISK: "warning",
        WildfirePrediction.HIGH_RISK: "danger",
    }
    return color_map.get(risk_level, "secondary")
