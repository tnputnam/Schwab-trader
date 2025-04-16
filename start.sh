#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Chrome is running with remote debugging
check_chrome_running() {
    pgrep -f "remote-debugging-port=9222" >/dev/null
    return $?
}

# Check if Python is installed
if ! command_exists python3; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    echo "pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Check if virtual environment exists, if not create it
if [ ! -d "schwab-trading-env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv schwab-trading-env
fi

# Activate virtual environment
echo "Activating virtual environment..."
source schwab-trading-env/bin/activate

# Install/upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in development mode
echo "Installing package in development mode..."
pip install -e .

# Check for config file
CONFIG_FILE=".env"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Creating .env file..."
    touch "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"  # Make it readable only by the user
fi

# Function to load environment variables
load_env_vars() {
    if [ -f "$CONFIG_FILE" ]; then
        echo "Loading environment variables from $CONFIG_FILE..."
        # Remove any existing export statements to avoid duplicates
        sed -i '/^export /d' "$CONFIG_FILE"
        # Load each line as an environment variable
        while IFS= read -r line; do
            if [[ ! -z "$line" && ! "$line" =~ ^# ]]; then
                export "$line"
            fi
        done < "$CONFIG_FILE"
    fi
}

# Function to save environment variable
save_env_var() {
    local var_name=$1
    local var_value=$2
    # Remove existing line if it exists
    sed -i "/^$var_name=/d" "$CONFIG_FILE"
    # Add new line
    echo "$var_name=$var_value" >> "$CONFIG_FILE"
    # Export the variable
    export "$var_name=$var_value"
}

# Load existing environment variables
load_env_vars

# Check if environment variables are set
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    echo "ALPHA_VANTAGE_API_KEY is not set. Please enter your Alpha Vantage API key:"
    read -r api_key
    save_env_var "ALPHA_VANTAGE_API_KEY" "$api_key"
    echo "API key saved to $CONFIG_FILE"
fi

if [ -z "$FLASK_SECRET_KEY" ]; then
    echo "FLASK_SECRET_KEY is not set. Generating a random key..."
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    save_env_var "FLASK_SECRET_KEY" "$secret_key"
    echo "Flask secret key saved to $CONFIG_FILE"
fi

# Verify environment variables are set
echo "Current environment variables:"
echo "ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY:0:4}..."  # Show first 4 chars only
echo "FLASK_SECRET_KEY: ${FLASK_SECRET_KEY:0:4}..."  # Show first 4 chars only

# Kill any existing Chrome instances on port 9222
pkill -f "chrome.*remote-debugging-port=9222"

# Start Chrome in debug mode
google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome-profile &

# Start the FastAPI server
python3 main.py

# Deactivate virtual environment when done
deactivate

# Start Chrome in debug mode
google-chrome --remote-debugging-port=9222 &

# Start Django server
python manage.py runserver &

# Wait for servers to start
sleep 5

# Open the dashboard in Chrome
google-chrome http://localhost:8000 &

# Function to handle import process
function handle_import() {
    # Start Selenium-controlled Chrome for Schwab import
    python manage.py runscript schwab_import
}

# Export the function so it can be used by the Django view
export -f handle_import

# Keep the script running
wait 