#!/usr/bin/env python
"""
This script directly runs the Django server without relying on manage.py
or virtual environments.
"""
import os
import sys
import importlib.util

# Configure the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildfire_prediction.settings')

try:
    # Try to import and load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("Warning: python-dotenv not found, environment variables may not be loaded")

try:
    # Try to import Django
    import django
    django.setup()
    
    # Get the server address
    from django.conf import settings
    DEBUG = getattr(settings, 'DEBUG', False)
    ALLOWED_HOSTS = getattr(settings, 'ALLOWED_HOSTS', ['localhost', '127.0.0.1'])
    
    # Import and run the development server
    from django.core.management.commands.runserver import Command as RunserverCommand
    
    server = RunserverCommand()
    server.handle(addrport="8000", use_ipv6=False, use_reloader=True)
    
except ImportError as e:
    print(f"Error: Could not import Django. Make sure it's installed: {e}")
    print("\nTry installing Django and other requirements with:")
    print("pip install django==5.0.2 python-dotenv==1.0.1 requests==2.31.0 django-leaflet==0.29.0 django-environ==0.11.2 gunicorn==21.2.0 whitenoise==6.6.0")
    sys.exit(1)
except Exception as e:
    print(f"Error starting Django server: {e}")
    sys.exit(1) 