@echo off
echo Starting Django development server...
set DJANGO_SETTINGS_MODULE=wildfire_prediction.settings
python -m django runserver
pause 