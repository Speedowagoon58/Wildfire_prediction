import requests
from django.conf import settings
from datetime import datetime
from django.utils import timezone
from .models import WeatherData
import logging

logger = logging.getLogger(__name__)


def fetch_current_weather(region):
    """
    Fetch current weather data from OpenWeatherMap API for a given region
    """
    params = {
        "lat": region.latitude,
        "lon": region.longitude,
        "appid": settings.OPENWEATHERMAP_API_KEY,
        "units": "metric",  # Use metric units
    }

    try:
        logger.info(f"Fetching weather data for {region.name} with params: {params}")
        response = requests.get(settings.OPENWEATHERMAP_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Create a dictionary with the weather data
        weather_data_dict = {
            "region": region,
            "timestamp": timezone.now(),
            "temperature": data["main"]["temp"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"],
            "wind_direction": data["wind"].get("deg", 0),
            "precipitation": data.get("rain", {}).get("1h", 0),  # Rain in last hour
            "pressure": data["main"]["pressure"],
        }

        # Create the WeatherData object
        weather_data = WeatherData.objects.create(**weather_data_dict)
        logger.info(f"Successfully created weather data for {region.name}")

        return weather_data

    except requests.RequestException as e:
        logger.error(f"Error fetching weather data for {region.name}: {str(e)}")
        return None
    except KeyError as e:
        logger.error(
            f"Missing data in weather API response for {region.name}: {str(e)}"
        )
        return None
    except Exception as e:
        logger.error(
            f"Unexpected error fetching weather data for {region.name}: {str(e)}"
        )
        return None


def update_weather_data():
    """
    Update weather data for all regions
    """
    from apps.core.models import Region

    for region in Region.objects.all():
        fetch_current_weather(region)


def fetch_historical_weather(region, start_date, end_date):
    """
    Fetch historical weather data from NOAA's Climate Data Online API for a given region and date range.
    """
    # NOAA CDO API endpoint
    base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/data"

    # Convert dates to required format
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Find the nearest NOAA station to the region
    station_id = find_nearest_noaa_station(region.latitude, region.longitude)
    if not station_id:
        return None

    params = {
        "datasetid": "GHCND",  # Global Historical Climatology Network - Daily
        "stationid": station_id,
        "startdate": start_date_str,
        "enddate": end_date_str,
        "datatypeid": [
            "TMAX",
            "TMIN",
            "PRCP",
            "AWND",
            "RHUM",
        ],  # Temperature, Precipitation, Wind, Humidity
        "limit": 1000,
        "units": "metric",
    }

    headers = {"token": settings.NOAA_API_KEY}

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Process the data into our format
        processed_data = []
        for result in data.get("results", []):
            date = datetime.strptime(result["date"], "%Y-%m-%dT%H:%M:%S")
            value = result["value"]
            datatype = result["datatype"]

            # Convert to our data format
            weather_data = {
                "date": date,
                "temperature": None,
                "humidity": None,
                "wind_speed": None,
                "precipitation": None,
            }

            if datatype == "TMAX":
                weather_data["temperature"] = (
                    value / 10
                )  # Convert from tenths of degrees C
            elif datatype == "PRCP":
                weather_data["precipitation"] = value / 10  # Convert from tenths of mm
            elif datatype == "AWND":
                weather_data["wind_speed"] = value / 10  # Convert from tenths of m/s
            elif datatype == "RHUM":
                weather_data["humidity"] = value

            processed_data.append(weather_data)

        return processed_data

    except requests.RequestException as e:
        print(f"Error fetching historical weather data for {region.name}: {str(e)}")
        return None


def find_nearest_noaa_station(latitude, longitude):
    """
    Find the nearest NOAA weather station to the given coordinates.
    """
    # NOAA station search endpoint
    base_url = "https://www.ncdc.noaa.gov/cdo-web/api/v2/stations"

    params = {
        "locationid": f"GHCND:{latitude},{longitude}",
        "limit": 1,
        "sortfield": "distance",
        "sortorder": "asc",
    }

    headers = {"token": settings.NOAA_API_KEY}

    try:
        response = requests.get(base_url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        if data.get("results"):
            return data["results"][0]["id"]
        return None

    except requests.RequestException as e:
        print(f"Error finding NOAA station: {str(e)}")
        return None


def fetch_dmn_historical_data(region, start_date, end_date):
    """
    Fetch historical weather data from DMN (Moroccan Meteorological Service) for a given region and date range.
    """
    # DMN API endpoint (this is a placeholder - you'll need to get the actual endpoint from DMN)
    base_url = "http://www.marocmeteo.ma/api/historical"

    # Convert dates to required format
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    # Find the nearest DMN station to the region
    station_id = find_nearest_dmn_station(region.latitude, region.longitude)
    if not station_id:
        return None

    params = {
        "station_id": station_id,
        "start_date": start_date_str,
        "end_date": end_date_str,
        "api_key": settings.DMN_API_KEY,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        # Process the data into our format
        processed_data = []
        for record in data.get("records", []):
            weather_data = {
                "date": datetime.strptime(record["date"], "%Y-%m-%d"),
                "temperature": record.get("temperature"),
                "humidity": record.get("humidity"),
                "wind_speed": record.get("wind_speed"),
                "precipitation": record.get("precipitation"),
                "pressure": record.get("pressure"),
            }
            processed_data.append(weather_data)

        return processed_data

    except requests.RequestException as e:
        print(f"Error fetching DMN historical data for {region.name}: {str(e)}")
        return None


def find_nearest_dmn_station(latitude, longitude):
    """
    Find the nearest DMN weather station to the given coordinates.
    """
    # DMN stations endpoint (placeholder)
    base_url = "http://www.marocmeteo.ma/api/stations"

    params = {
        "lat": latitude,
        "lon": longitude,
        "radius": 50,  # Search within 50km radius
        "api_key": settings.DMN_API_KEY,
    }

    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("stations"):
            # Return the closest station
            return data["stations"][0]["id"]
        return None

    except requests.RequestException as e:
        print(f"Error finding DMN station: {str(e)}")
        return None
