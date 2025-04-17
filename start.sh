#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to kill existing Flask server
kill_flask_server() {
    log_message "Checking for existing Flask server..."
    if pgrep -f "flask run" > /dev/null; then
        log_message "Stopping existing Flask server..."
        pkill -f "flask run"
        sleep 2  # Give it time to shut down gracefully
    fi
    
    # Double check if port is still in use
    if lsof -i :5000 > /dev/null; then
        log_message "Force closing port 5000..."
        kill $(lsof -t -i:5000) 2>/dev/null || true
        sleep 1
    fi
}

# Check if Python is installed
if ! command_exists python3; then
    log_message "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command_exists pip3; then
    log_message "Error: pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Kill any existing Flask server
kill_flask_server

# Check if virtual environment exists, if not create it
if [ ! -d "schwab-trading-env" ]; then
    log_message "Creating virtual environment..."
    python3 -m venv schwab-trading-env
fi

# Activate virtual environment
log_message "Activating virtual environment..."
source schwab-trading-env/bin/activate

# Install/upgrade pip
log_message "Upgrading pip..."
pip install --upgrade pip

# Install requirements
log_message "Installing requirements..."
pip install Flask==2.2.5 \
    Flask-SQLAlchemy==3.0.5 \
    Flask-Login==0.6.2 \
    Flask-Caching==2.0.2 \
    Werkzeug==2.2.3 \
    pandas==2.1.3 \
    numpy==1.26.2 \
    matplotlib==3.8.2 \
    yfinance==0.2.31 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    sqlalchemy==2.0.23

# Check for config file
CONFIG_FILE=".env"
if [ ! -f "$CONFIG_FILE" ]; then
    log_message "Creating .env file..."
    touch "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"  # Make it readable only by the user
fi

# Function to load environment variables
load_env_vars() {
    if [ -f "$CONFIG_FILE" ]; then
        log_message "Loading environment variables from $CONFIG_FILE..."
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
    sed -i "/^$var_name=/d" "$CONFIG_FILE"
    echo "$var_name=$var_value" >> "$CONFIG_FILE"
    export "$var_name=$var_value"
}

# Load existing environment variables
load_env_vars

# Check if environment variables are set
if [ -z "$ALPHA_VANTAGE_API_KEY" ]; then
    log_message "ALPHA_VANTAGE_API_KEY is not set. Please enter your Alpha Vantage API key:"
    read -r api_key
    save_env_var "ALPHA_VANTAGE_API_KEY" "$api_key"
    log_message "API key saved to $CONFIG_FILE"
fi

# Set Flask environment variables
export FLASK_APP=schwab_trader
export FLASK_DEBUG=1  # Using FLASK_DEBUG instead of deprecated FLASK_ENV

# Initialize/upgrade the database
log_message "Initializing/upgrading the database..."
if [ -f "create_db.py" ]; then
    python create_db.py
fi

# Start the Flask server
log_message "Starting Flask server..."
flask run --host=0.0.0.0 --port=5000 2>&1 | tee -a logs/server.log

# If the server crashes, log the error
if [ $? -ne 0 ]; then
    log_message "Error: Server crashed. Check logs/server.log for details."
    exit 1
fi

# Trap script exit and cleanup
cleanup() {
    log_message "Shutting down..."
    kill_flask_server
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
    fi
}

trap cleanup EXIT

# Keep the script running
wait 