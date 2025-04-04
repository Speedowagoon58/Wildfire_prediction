"""
Global risk factors and patterns for wildfire prediction.
This module contains data and analysis methods based on global wildfire patterns.
"""

# Global soil type risk factors based on research and historical data
GLOBAL_SOIL_RISK_FACTORS = {
    "Clay": {
        "base_risk": 0.7,
        "moisture_retention_impact": 0.8,
        "seasonal_variation": {
            "summer": 1.2,  # Higher risk in summer due to cracking
            "winter": 0.6,
            "spring": 0.8,
            "autumn": 0.7,
        },
        "drought_multiplier": 1.3,  # Impact during drought conditions
    },
    "Sandy": {
        "base_risk": 1.3,
        "moisture_retention_impact": 0.3,
        "seasonal_variation": {
            "summer": 1.5,  # Higher risk due to quick drying
            "winter": 0.8,
            "spring": 1.1,
            "autumn": 1.0,
        },
        "drought_multiplier": 1.6,
    },
    "Loam": {
        "base_risk": 1.0,
        "moisture_retention_impact": 0.6,
        "seasonal_variation": {
            "summer": 1.3,
            "winter": 0.7,
            "spring": 0.9,
            "autumn": 0.8,
        },
        "drought_multiplier": 1.4,
    },
}

# Global vegetation density impact factors
VEGETATION_DENSITY_FACTORS = {
    "sparse": (0.0, 0.3, 0.8),  # Low fuel load
    "moderate": (0.3, 0.6, 1.2),  # Medium fuel load
    "dense": (0.6, 1.0, 1.5),  # High fuel load
}

# Historical global wildfire patterns by climate zone
CLIMATE_ZONE_PATTERNS = {
    "mediterranean": {
        "peak_season": ["july", "august"],
        "risk_multiplier": 1.4,
        "drought_sensitivity": 1.5,
    },
    "semi_arid": {
        "peak_season": ["june", "july", "august", "september"],
        "risk_multiplier": 1.3,
        "drought_sensitivity": 1.6,
    },
    "temperate": {
        "peak_season": ["august", "september"],
        "risk_multiplier": 1.1,
        "drought_sensitivity": 1.2,
    },
}


def get_season(month):
    """Determine season based on month number."""
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"


def calculate_soil_risk_factor(soil_type, current_month, drought_index=None):
    """Calculate soil-based risk factor considering season and conditions."""
    if soil_type.name not in GLOBAL_SOIL_RISK_FACTORS:
        return 1.0  # Default risk factor

    soil_data = GLOBAL_SOIL_RISK_FACTORS[soil_type.name]
    season = get_season(current_month)

    # Base calculation
    risk_factor = soil_data["base_risk"]

    # Apply seasonal variation
    risk_factor *= soil_data["seasonal_variation"][season]

    # Apply moisture retention impact
    moisture_impact = (
        soil_data["moisture_retention_impact"] * soil_type.moisture_retention
    )
    risk_factor *= (
        2 - moisture_impact
    )  # Invert moisture retention (higher retention = lower risk)

    # Apply drought conditions if available
    if drought_index and drought_index > 1:
        drought_impact = min(drought_index - 1, 1) * (
            soil_data["drought_multiplier"] - 1
        )
        risk_factor *= 1 + drought_impact

    return risk_factor


def calculate_vegetation_risk_factor(density):
    """Calculate vegetation-based risk factor."""
    if density <= VEGETATION_DENSITY_FACTORS["sparse"][1]:
        return VEGETATION_DENSITY_FACTORS["sparse"][2]
    elif density <= VEGETATION_DENSITY_FACTORS["moderate"][1]:
        return VEGETATION_DENSITY_FACTORS["moderate"][2]
    else:
        return VEGETATION_DENSITY_FACTORS["dense"][2]


def calculate_climate_risk_multiplier(month, climate_zone="mediterranean"):
    """Calculate climate-based risk multiplier."""
    if climate_zone not in CLIMATE_ZONE_PATTERNS:
        return 1.0

    pattern = CLIMATE_ZONE_PATTERNS[climate_zone]
    month_name = [
        "january",
        "february",
        "march",
        "april",
        "may",
        "june",
        "july",
        "august",
        "september",
        "october",
        "november",
        "december",
    ][month - 1]

    # Higher risk during peak season
    if month_name in pattern["peak_season"]:
        return pattern["risk_multiplier"]

    # Reduced risk outside peak season
    return 1.0
