// Utility function to format temperature
function formatTemperature(temp) {
  return `${Math.round(temp)}°C`;
}

// Utility function to format wind speed
function formatWindSpeed(speed) {
  return `${Math.round(speed)} km/h`;
}

// Calculate risk level based on weather parameters
function calculateRiskLevel(temperature, humidity, windSpeed) {
  let riskScore = 0;

  // Temperature risk (higher temperature = higher risk)
  if (temperature > 35) riskScore += 3;
  else if (temperature > 30) riskScore += 2;
  else if (temperature > 25) riskScore += 1;

  // Humidity risk (lower humidity = higher risk)
  if (humidity < 30) riskScore += 3;
  else if (humidity < 40) riskScore += 2;
  else if (humidity < 50) riskScore += 1;

  // Wind speed risk (higher wind speed = higher risk)
  if (windSpeed > 30) riskScore += 3;
  else if (windSpeed > 20) riskScore += 2;
  else if (windSpeed > 10) riskScore += 1;

  // Determine risk level based on total score
  if (riskScore >= 7) return "high";
  if (riskScore >= 4) return "moderate";
  return "low";
}

// Update risk indicator element
function updateRiskIndicator(element, riskLevel) {
  element.className = "risk-indicator";
  element.classList.add(`risk-${riskLevel}`);

  let message = "";
  switch (riskLevel) {
    case "high":
      message = "High Risk - Exercise Extreme Caution";
      break;
    case "moderate":
      message = "Moderate Risk - Stay Alert";
      break;
    case "low":
      message = "Low Risk - Normal Conditions";
      break;
  }

  element.textContent = message;
}

// Initialize map
function initializeMap(containerId, center = [-7.0926, 31.7917], zoom = 6) {
  const map = new ol.Map({
    target: containerId,
    layers: [
      new ol.layer.Tile({
        source: new ol.source.OSM(),
      }),
    ],
    view: new ol.View({
      center: ol.proj.fromLonLat(center),
      zoom: zoom,
    }),
  });

  return map;
}

// Add marker to map
function addMarker(map, coordinates, popupContent) {
  const marker = new ol.Feature({
    geometry: new ol.geom.Point(ol.proj.fromLonLat(coordinates)),
  });

  const vectorSource = new ol.source.Vector({
    features: [marker],
  });

  const vectorLayer = new ol.layer.Vector({
    source: vectorSource,
    style: new ol.style.Style({
      image: new ol.style.Circle({
        radius: 6,
        fill: new ol.style.Fill({ color: "#ff0000" }),
        stroke: new ol.style.Stroke({ color: "#ffffff", width: 2 }),
      }),
    }),
  });

  map.addLayer(vectorLayer);

  // Add popup
  const element = document.createElement("div");
  element.className = "ol-popup";
  element.innerHTML = popupContent;

  const popup = new ol.Overlay({
    element: element,
    positioning: "bottom-center",
    stopEvent: false,
    offset: [0, -10],
  });
  map.addOverlay(popup);

  // Show popup on click
  map.on("click", function (evt) {
    const feature = map.forEachFeatureAtPixel(evt.pixel, function (feature) {
      return feature;
    });

    if (feature) {
      const coordinates = feature.getGeometry().getCoordinates();
      popup.setPosition(coordinates);
    } else {
      popup.setPosition(undefined);
    }
  });
}

// Initialize map markers with weather data
function initializeMapMarkers(map, locations) {
  locations.forEach((location) => {
    const popupContent = `
      <strong>${location.name}</strong><br>
      Temperature: ${formatTemperature(location.temperature)}<br>
      Humidity: ${location.humidity}%<br>
      Wind Speed: ${formatWindSpeed(location.windSpeed)}
    `;
    addMarker(map, [location.lng, location.lat], popupContent);
  });
}

// Handle region selection change
function handleRegionChange(selectElement) {
  const regionId = selectElement.value;
  if (regionId) {
    // Fetch weather data for the selected region
    fetch(`/api/weather/${regionId}/`)
      .then((response) => response.json())
      .then((data) => {
        // Update the weather display
        updateWeatherDisplay(data);
        // Update the risk indicator
        const riskLevel = calculateRiskLevel(
          data.temperature,
          data.humidity,
          data.windSpeed
        );
        const riskElement = document.querySelector(".risk-indicator");
        if (riskElement) {
          updateRiskIndicator(riskElement, riskLevel);
        }
      })
      .catch((error) => console.error("Error fetching weather data:", error));
  }
}

// Document ready handler
document.addEventListener("DOMContentLoaded", function () {
  // Initialize any necessary components
  const regionSelect = document.querySelector(".region-select select");
  if (regionSelect) {
    regionSelect.addEventListener("change", function () {
      handleRegionChange(this);
    });
  }

  // Initialize map if container exists
  const mapContainer = document.getElementById("map");
  if (mapContainer) {
    const map = initializeMap("map");
    // You can load initial markers here if needed
  }
});
