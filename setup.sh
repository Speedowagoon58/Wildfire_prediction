#!/bin/bash
# This script sets up the development environment for the Wildfire Risk Monitoring project

# Output with colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Clean up any existing virtual environments
echo -e "${GREEN}Cleaning up old virtual environments...${NC}"
rm -rf venv venv_new myenv env_fresh 2>/dev/null

# Create a new virtual environment
echo -e "${GREEN}Creating a new virtual environment...${NC}"
python3 -m venv venv

# Activate the virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${GREEN}Installing dependencies...${NC}"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Ensure .env file exists
if [ ! -f .env ]; then
    echo -e "${GREEN}Creating .env file from example...${NC}"
    cp .env-example .env
    echo -e "${YELLOW}Please update the .env file with your actual values.${NC}"
fi

# Run migrations
echo -e "${GREEN}Running database migrations...${NC}"
python manage.py migrate

# Collect static files
echo -e "${GREEN}Collecting static files...${NC}"
python manage.py collectstatic --noinput

echo -e "${GREEN}Setup complete! Run 'python manage.py runserver' to start the development server.${NC}"
echo -e "${GREEN}To create an admin user, run 'python manage.py createsuperuser'.${NC}" 