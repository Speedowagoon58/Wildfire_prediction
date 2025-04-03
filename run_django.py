#!/usr/bin/env python
"""
Direct Django runner script that bypasses virtual environment issues.
This script sets up the Django environment and runs the development server.
"""

import os
import sys
import importlib.util
from django.core.management import execute_from_command_line

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "wildfire_prediction.settings")

# Try to load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    print(
        "Warning: python-dotenv not installed. Environment variables may not be loaded."
    )

# Import Django and set it up
import django

django.setup()

# Get server settings
from django.conf import settings

print(f"Debug mode: {settings.DEBUG}")
print(f"Allowed hosts: {settings.ALLOWED_HOSTS}")

print("\nStarting Django development server...")
print("Press Ctrl+C to stop the server")
print("\nYou can access your site at:")
print("http://127.0.0.1:8000/")
print("http://localhost:8000/")

# Run the server using manage.py command
execute_from_command_line(["manage.py", "runserver", "8000"])
