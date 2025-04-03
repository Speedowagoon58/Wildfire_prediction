# This script sets up the development environment for the Wildfire Risk Monitoring project

# Set execution policy for this process
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force

# Clean up any existing virtual environments
Write-Host "Cleaning up old virtual environments..." -ForegroundColor Green
If (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
}
If (Test-Path "venv_new") {
    Remove-Item -Recurse -Force "venv_new" -ErrorAction SilentlyContinue
}
If (Test-Path "myenv") {
    Remove-Item -Recurse -Force "myenv" -ErrorAction SilentlyContinue
}
If (Test-Path "env_fresh") {
    Remove-Item -Recurse -Force "env_fresh" -ErrorAction SilentlyContinue
}

# Create a new virtual environment
Write-Host "Creating a new virtual environment..." -ForegroundColor Green
python -m venv venv

# Activate the virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
.\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Green
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Ensure .env file exists
if (-Not (Test-Path ".env")) {
    Write-Host "Creating .env file from example..." -ForegroundColor Green
    Copy-Item ".env-example" ".env"
    Write-Host "Please update the .env file with your actual values." -ForegroundColor Yellow
}

# Run migrations
Write-Host "Running database migrations..." -ForegroundColor Green
python manage.py migrate

# Collect static files
Write-Host "Collecting static files..." -ForegroundColor Green
python manage.py collectstatic --noinput

Write-Host "Setup complete! Run 'python manage.py runserver' to start the development server." -ForegroundColor Green
Write-Host "To create an admin user, run 'python manage.py createsuperuser'." -ForegroundColor Green 