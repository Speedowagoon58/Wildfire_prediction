# Wildfire Risk Monitoring for Morocco

A Django-based web application for monitoring wildfire risks and historical data across Morocco.

## Features

- Real-time weather data monitoring using OpenWeatherMap API
- Historical wildfire data visualization
- Interactive mapping of wildfire risk areas
- Responsive design for all devices

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git

## Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd wildfire_prediction
   ```

2. **Create and activate a virtual environment**

   For Windows:

   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # For PowerShell
   # OR
   .\venv\Scripts\activate.bat  # For Command Prompt
   ```

   For macOS/Linux:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**

   Copy the example environment file and update with your values:

   ```bash
   cp .env-example .env
   ```

   Then edit the `.env` file with your actual values, particularly:

   - `SECRET_KEY`: Your Django secret key
   - `OPENWEATHER_API_KEY`: Your OpenWeatherMap API key

5. **Run database migrations**

   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (admin)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Collect static files**

   ```bash
   python manage.py collectstatic
   ```

## Running the Application

### Development Server

```bash
python manage.py runserver
```

The application will be available at http://127.0.0.1:8000/

### Accessing the Admin Panel

Visit http://127.0.0.1:8000/admin/ and login with the superuser credentials you created.

## Troubleshooting

### Virtual Environment Issues

If you have problems with the virtual environment:

1. Make sure PowerShell execution policy allows running scripts (Windows):

   ```bash
   Set-ExecutionPolicy RemoteSigned -Scope Process
   ```

2. If packages are being installed in the user location instead of the virtual environment:
   ```bash
   python -m pip install --force-reinstall -r requirements.txt
   ```

### Module Not Found Errors

If Django or other modules are not found:

1. Ensure you've activated the virtual environment
2. Try reinstalling the package directly:
   ```bash
   pip install django==5.0.2
   ```

## Deployment

For production deployment:

1. Set `DEBUG=False` in your `.env` file
2. Configure proper `ALLOWED_HOSTS` in your `.env` file
3. Enable all security settings in `.env`:

   ```
   SECURE_SSL_REDIRECT=True
   SESSION_COOKIE_SECURE=True
   CSRF_COOKIE_SECURE=True
   ```

4. Use a production-ready server like Gunicorn:
   ```bash
   gunicorn wildfire_prediction.wsgi:application
   ```

## License

[MIT License](LICENSE)
