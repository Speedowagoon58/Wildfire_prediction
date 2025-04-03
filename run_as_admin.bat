@echo off
echo Starting Django server with administrator privileges...

:: Set Django environment variable
set DJANGO_SETTINGS_MODULE=wildfire_prediction.settings

:: Run the script with admin rights
powershell -Command "Start-Process python -ArgumentList 'run_django.py' -Verb RunAs"

echo Server started in a new window with administrator privileges.
echo You can access your site at http://127.0.0.1:8000/
pause 