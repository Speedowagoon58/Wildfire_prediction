# Wildfire Prediction System

A web-based system that helps predict and monitor wildfire risks across different regions in Morocco. It combines real-time weather data with historical patterns to provide accurate risk assessments.

## What It Does

- Tracks weather conditions in real-time
- Analyzes historical data to spot patterns
- Shows risk levels on an interactive map
- Provides detailed predictions for each region
- Updates automatically every 15 minutes

## Getting Started

1. Clone the repo:

   ```bash
   git clone https://github.com/Speedowagoon58/wildfire_prediction.git
   cd wildfire_prediction
   ```

2. Set up your environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install -r requirements.txt
   ```

3. Configure settings:

   ```bash
   cp .env.example .env
   # Add your API keys and settings to .env
   ```

4. Start the server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

## Key Features

### Weather Tracking

- Temperature
- Humidity
- Wind speed and direction
- Precipitation levels

### Risk Assessment

- Low, Medium, High risk levels
- Real-time updates
- Historical pattern analysis
- Geographic risk mapping

### Data Management

- Efficient database design
- Quick data retrieval
- Secure data handling
- Regular backups

## Tech Stack

- Django for the backend
- PostgreSQL for data storage
- REST APIs for data access
- Machine learning for predictions

## Need Help?

Open an issue in the GitHub repository or contact me.

## Credits

- Weather data from OpenWeatherMap
- Built with Django
- Huge help from AI in all stages
- Thank you ALX.
