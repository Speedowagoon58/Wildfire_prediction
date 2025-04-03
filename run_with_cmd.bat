@echo off
echo Starting Django server using command prompt...

:: Set Django environment variable
set DJANGO_SETTINGS_MODULE=wildfire_prediction.settings

:: Check if Python is available and install packages if needed
python -c "import django" 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Django not found. Attempting to install...
    python -m pip install django==5.0.2 python-dotenv==1.0.1 requests==2.31.0 django-leaflet==0.29.0 django-environ==0.11.2 gunicorn==21.2.0 whitenoise==6.6.0
)

:: Run Django server directly
echo Starting Django server...
python direct_run.py

pause 