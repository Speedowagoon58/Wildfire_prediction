import os
import sys
import django

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wildfire_prediction.settings')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Initialize Django
django.setup()

# Run the development server
from django.core.management import execute_from_command_line
if __name__ == '__main__':
    print("Starting Django development server...")
    execute_from_command_line(['manage.py', 'runserver'])
    # This is equivalent to: python manage.py runserver 