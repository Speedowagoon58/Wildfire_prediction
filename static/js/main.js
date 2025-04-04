import { animations, LoadingSpinner, ProgressBar } from "./animations.js";
import themeManager from "./theme.js";

// Utility function to format temperature
function formatTemperature(temp) {
  return `${Math.round(temp)}°C`;
}

// Utility function to format wind speed
function formatWindSpeed(speed) {
  return `${Math.round(speed)} km/h`;
}

// Loading state management for content sections
function showContentLoading(element) {
  element.classList.add("content-loading");
}

function hideContentLoading(element) {
  element.classList.remove("content-loading");
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
    const weatherCard = document.querySelector(".weather-card");
    const riskIndicator = document.querySelector(".risk-indicator");

    if (weatherCard) showContentLoading(weatherCard);
    if (riskIndicator) showContentLoading(riskIndicator);

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
        if (riskIndicator) {
          updateRiskIndicator(riskIndicator, riskLevel);
          hideContentLoading(riskIndicator);
        }
        if (weatherCard) hideContentLoading(weatherCard);
      })
      .catch((error) => {
        console.error("Error fetching weather data:", error);
        if (weatherCard) hideContentLoading(weatherCard);
        if (riskIndicator) hideContentLoading(riskIndicator);
      });
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
    showContentLoading(mapContainer);
    const map = initializeMap("map");
    // Load initial markers
    Promise.all([fetchWeatherData("initial"), fetchPredictions("initial")])
      .then(([weatherData, predictionsData]) => {
        initializeMapMarkers(map, weatherData.locations);
        hideContentLoading(mapContainer);
      })
      .catch((error) => {
        console.error("Error initializing map:", error);
        hideContentLoading(mapContainer);
      });
  }

  // Initialize tooltips
  var tooltipTriggerList = [].slice.call(
    document.querySelectorAll('[data-bs-toggle="tooltip"]')
  );
  var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl);
  });

  // Add fade-in animation to dashboard cards
  const cards = document.querySelectorAll(".dashboard-card");
  cards.forEach((card, index) => {
    card.style.animation = `fadeIn 0.5s ease-in forwards ${index * 0.1}s`;
  });

  // Initialize loading spinner
  const loadingSpinner = new LoadingSpinner(
    document.getElementById("loading-container")
  );

  // Initialize progress bar
  const progressBar = new ProgressBar(
    document.getElementById("progress-container")
  );

  // Function to update weather data
  async function updateWeatherData() {
    try {
      loadingSpinner.show();
      progressBar.show();
      progressBar.setProgress(0);

      const response = await fetch("/api/weather-data");
      const data = await response.json();

      // Update weather grid
      const weatherGrid = document.querySelector(".weather-grid");
      if (weatherGrid) {
        weatherGrid.innerHTML = "";
        data.forEach((item, index) => {
          const weatherItem = document.createElement("div");
          weatherItem.className = "weather-item";
          weatherItem.innerHTML = `
            <i class="fas fa-${getWeatherIcon(item.condition)}"></i>
            <h3>${item.location}</h3>
            <p>${item.temperature}°C</p>
            <p>${item.humidity}% Humidity</p>
          `;

          weatherGrid.appendChild(weatherItem);
          animations.fadeIn(weatherItem, 300);
          progressBar.setProgress(((index + 1) / data.length) * 100);
        });
      }
    } catch (error) {
      console.error("Error updating weather data:", error);
      showError("Failed to update weather data");
    } finally {
      loadingSpinner.hide();
      setTimeout(() => {
        progressBar.hide();
      }, 500);
    }
  }

  // Function to update risk levels
  async function updateRiskLevels() {
    try {
      const response = await fetch("/api/risk-levels");
      const data = await response.json();

      // Update risk level indicators
      const riskContainer = document.querySelector(".risk-container");
      if (riskContainer) {
        riskContainer.innerHTML = "";
        data.forEach((risk) => {
          const riskElement = document.createElement("div");
          riskElement.className = `risk-level ${risk.level.toLowerCase()}`;
          riskElement.textContent = `${risk.area}: ${risk.level} Risk`;
          riskContainer.appendChild(riskElement);
          animations.slideDown(riskElement, 300);
        });
      }
    } catch (error) {
      console.error("Error updating risk levels:", error);
      showError("Failed to update risk levels");
    }
  }

  // Function to show error messages
  function showError(message) {
    const errorContainer = document.getElementById("error-container");
    if (errorContainer) {
      const errorElement = document.createElement("div");
      errorElement.className = "alert alert-danger";
      errorElement.textContent = message;
      errorContainer.appendChild(errorElement);
      animations.shake(errorElement);

      setTimeout(() => {
        animations.fadeOut(errorElement, 300);
        setTimeout(() => {
          errorElement.remove();
        }, 300);
      }, 3000);
    }
  }

  // Function to get weather icon based on condition
  function getWeatherIcon(condition) {
    const icons = {
      clear: "sun",
      cloudy: "cloud",
      rain: "cloud-rain",
      storm: "bolt",
      snow: "snowflake",
    };
    return icons[condition.toLowerCase()] || "question";
  }

  // Event listeners
  document.addEventListener("DOMContentLoaded", () => {
    // Initialize map
    initMap();

    // Initial data load
    updateWeatherData();
    updateRiskLevels();

    // Set up refresh button
    const refreshButton = document.getElementById("refresh-button");
    if (refreshButton) {
      refreshButton.addEventListener("click", () => {
        animations.pulse(refreshButton);
        updateWeatherData();
        updateRiskLevels();
      });
    }

    // Set up auto-refresh
    setInterval(() => {
      updateWeatherData();
      updateRiskLevels();
    }, 300000); // Refresh every 5 minutes

    // Theme change listener
    window.addEventListener("themechange", (e) => {
      // Update map tiles if needed
      const map = document.querySelector("#map");
      if (map && map._leaflet_id) {
        const isDark = e.detail.theme === "dark";
        const tileLayer = document.querySelector(".leaflet-tile-pane");
        if (tileLayer) {
          tileLayer.style.filter = isDark
            ? "invert(90%) hue-rotate(180deg)"
            : "none";
        }
      }
    });
  });
});

// API handling functions
async function fetchWeatherData(regionId) {
  const weatherSection = document.querySelector(".weather-section");
  if (weatherSection) showContentLoading(weatherSection);

  try {
    const response = await fetch(`/api/weather/current/${regionId}/`);
    if (!response.ok) throw new Error("Weather data fetch failed");
    const data = await response.json();
    if (weatherSection) hideContentLoading(weatherSection);
    return data;
  } catch (error) {
    console.error("Error:", error);
    if (weatherSection) hideContentLoading(weatherSection);
    throw error;
  }
}

async function fetchPredictions(regionId) {
  const predictionsSection = document.querySelector(".predictions-section");
  if (predictionsSection) showContentLoading(predictionsSection);

  try {
    const response = await fetch(`/api/predictions/${regionId}/`);
    if (!response.ok) throw new Error("Predictions fetch failed");
    const data = await response.json();
    if (predictionsSection) hideContentLoading(predictionsSection);
    return data;
  } catch (error) {
    console.error("Error:", error);
    if (predictionsSection) hideContentLoading(predictionsSection);
    throw error;
  }
}

// Utility functions
function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getRiskLevelClass(riskLevel) {
  if (riskLevel < 0.25) return "risk-low";
  if (riskLevel < 0.5) return "risk-medium";
  if (riskLevel < 0.75) return "risk-high";
  return "risk-extreme";
}

// Error handling
function handleApiError(error, elementId, message = "An error occurred") {
  console.error(error);
  const element = document.getElementById(elementId);
  if (element) {
    element.innerHTML = `
      <div class="alert alert-danger">
        ${message}
        <br>
        <small>${error.message}</small>
      </div>
    `;
  }
}

// Animation utilities
function fadeIn(element, duration = 500) {
  element.style.opacity = 0;
  element.style.display = "block";

  let start = null;
  function animate(timestamp) {
    if (!start) start = timestamp;
    const progress = timestamp - start;
    element.style.opacity = Math.min(progress / duration, 1);
    if (progress < duration) {
      window.requestAnimationFrame(animate);
    }
  }
  window.requestAnimationFrame(animate);
}

// Add CSS animation for fade-in effect
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);
