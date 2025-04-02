# Wildfire Risk Monitoring & Historical Data Dashboard for Morocco

A web application designed to display key environmental factors contributing to wildfire risk and visualize historical wildfire data across different regions of Morocco.

## Features

- Real-time weather data display (temperature, humidity, wind speed)
- Interactive map visualization using Leaflet.js
- Region selection functionality
- Historical wildfire data display (where available)
- Basic risk indicators based on current weather conditions

## Project Structure

```
wildfire_prediction/
├── core/               # Base templates and main dashboard
├── weather/           # Weather API integration
├── mapping/          # Map display and region definitions
└── historical_data/  # Historical fire data management
```

## Setup

1. Clone the repository:

```bash
git clone [your-repository-url]
cd wildfire_prediction
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   Create a `.env` file in the root directory with:

```
DEBUG=True
SECRET_KEY=your-secret-key
OPENWEATHER_API_KEY=your-api-key
```

5. Run migrations:

```bash
python manage.py migrate
```

6. Start the development server:

```bash
python manage.py runserver
```

## API Endpoints

- `/`: Main dashboard
- `/api/weather/{region_id}/`: Current weather data
- `/api/regions/`: Map regions data
- `/historical/`: Historical fire data display
- `/api/historical-fires/`: Historical fire data API

## Data Sources

- Weather Data: OpenWeatherMap API
- Historical Data: Various sources (documented in the application)

## Contributing

This is a capstone project. For any questions or suggestions, please open an issue.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
