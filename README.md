# Wildfire Prediction System

A Django-based system for predicting and monitoring wildfire risks using weather data and historical patterns.

## Features

- Real-time weather data integration
- Historical data analysis
- Interactive mapping
- API documentation
- Monitoring and logging
- Rate limiting and security features

## Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

## Local Development Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/wildfire_prediction.git
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

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run migrations:

   ```bash
   python manage.py migrate
   ```

6. Create a superuser:

   ```bash
   python manage.py createsuperuser
   ```

7. Run the development server:

   ```bash
   python manage.py runserver
   ```

## Docker Development Setup

1. Build and start the containers:

   ```bash
   docker-compose up --build
   ```

2. Run migrations:

   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. Create a superuser:

   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

## Testing

Run tests with coverage:

```bash
pytest --cov=. --cov-report=term-missing
```

## Code Quality

The project uses several tools to maintain code quality:

- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking
- bandit for security checks

Run all checks:

```bash
pre-commit run --all-files
```

## API Documentation

API documentation is available at `/api/docs/` when running the server.

## Deployment

1. Set up production environment variables
2. Build and push Docker image
3. Deploy using your preferred platform (e.g., AWS, GCP, Heroku)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

## Acknowledgments

- OpenWeatherMap API for weather data
- Django framework
- Leaflet for map visualization
- All contributors and maintainers
