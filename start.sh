#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages with timestamps
log_message() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        return 1
    fi
    return 0
}

# Function to check disk space
check_disk_space() {
    local required_space=1000  # 1GB in MB
    local available_space=$(df -m . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt "$required_space" ]; then
        log_message "Error: Insufficient disk space. Required: ${required_space}MB, Available: ${available_space}MB"
        return 1
    fi
    return 0
}

# Function to kill existing Flask server
kill_flask_server() {
    log_message "Checking for existing Flask server..."
    if pgrep -f "python -m flask" > /dev/null; then
        log_message "Stopping existing Flask server..."
        pkill -f "python -m flask"
        sleep 2  # Give it time to shut down gracefully
        
        # Double check if port is still in use
        if ! check_port 5000; then
            log_message "Force closing port 5000..."
            kill $(lsof -t -i:5000) 2>/dev/null || true
            sleep 1
        fi
    fi
}

# Function to validate environment variables
validate_env_vars() {
    local required_vars=(
        "FLASK_APP"
        "FLASK_ENV"
        "SECRET_KEY"
        "DATABASE_URL"
        "SCHWAB_API_KEY"
        "SCHWAB_API_SECRET"
        "SCHWAB_API_BASE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_message "Error: Required environment variable $var is not set"
            return 1
        fi
    done
    return 0
}

# Function to safely load environment variables
load_env_vars() {
    if [ -f "$CONFIG_FILE" ]; then
        log_message "Loading environment variables from $CONFIG_FILE..."
        # Use python to safely parse the .env file
        python3 - << EOF
import os
from dotenv import load_dotenv
load_dotenv('$CONFIG_FILE')
for key, value in os.environ.items():
    if key.startswith(('FLASK_', 'DATABASE_', 'SCHWAB_', 'SECRET_')):
        print(f"export {key}='{value}'")
EOF
    fi
}

# Function to check if requirements are up to date
check_requirements() {
    if [ -f "requirements.txt" ]; then
        log_message "Checking if requirements are up to date..."
        pip freeze | sort > current_requirements.txt
        sort requirements.txt > sorted_requirements.txt
        if ! diff -q current_requirements.txt sorted_requirements.txt > /dev/null; then
            return 1
        fi
        rm current_requirements.txt sorted_requirements.txt
    fi
    return 0
}

# Function to initialize database
initialize_database() {
    log_message "Initializing/upgrading the database..."
    if [ -f "create_db.py" ]; then
        if ! python create_db.py; then
            log_message "Error: Database initialization failed"
            return 1
        fi
    fi
    return 0
}

# Main script starts here
set -e  # Exit on any error

# Check prerequisites
if ! command_exists python3; then
    log_message "Error: Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

if ! command_exists pip3; then
    log_message "Error: pip3 is not installed. Please install pip3 and try again."
    exit 1
fi

# Check disk space
if ! check_disk_space; then
    exit 1
fi

# Create necessary directories
log_message "Creating required directories..."
mkdir -p logs sessions data

# Kill any existing Flask server
kill_flask_server

# Activate virtual environment
log_message "Activating virtual environment..."
if [ ! -d "venv" ]; then
    log_message "Creating virtual environment..."
    if ! python3 -m venv venv; then
        log_message "Error: Failed to create virtual environment"
        exit 1
    fi
fi
source venv/bin/activate

# Install/upgrade pip
log_message "Upgrading pip..."
pip install --upgrade pip

# Install requirements if needed
if [ ! -f "requirements.txt" ]; then
    log_message "Creating requirements.txt..."
    cat > requirements.txt << EOL
Flask==2.2.5
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-Caching==2.0.2
Werkzeug==2.2.3
pandas==2.1.3
numpy==1.26.2
matplotlib==3.8.2
yfinance==0.2.31
python-dotenv==1.0.0
requests==2.31.0
requests_oauthlib==1.3.1
sqlalchemy==2.0.23
alembic==1.12.1
EOL
fi

if ! check_requirements; then
    log_message "Installing/updating requirements..."
    if ! pip install -r requirements.txt; then
        log_message "Error: Failed to install requirements"
        exit 1
    fi
fi

# Check for config file
CONFIG_FILE=".env"
if [ ! -f "$CONFIG_FILE" ]; then
    log_message "Creating .env file..."
    cat > "$CONFIG_FILE" << EOL
# Flask Configuration
FLASK_APP=schwab_trader
FLASK_ENV=development
SECRET_KEY=$(openssl rand -hex 32)

# Database Configuration
DATABASE_URL=sqlite:///data/schwab_trader.db

# Logging Configuration
LOG_LEVEL=INFO
LOG_DIR=logs

# Session Configuration
SESSION_TYPE=filesystem
SESSION_FILE_DIR=sessions
SESSION_PERMANENT=true
PERMANENT_SESSION_LIFETIME=3600

# API Configuration
SCHWAB_API_KEY=your_api_key_here
SCHWAB_API_SECRET=your_api_secret_here
SCHWAB_API_BASE_URL=https://api.schwab.com
EOL
    chmod 600 "$CONFIG_FILE"  # Make it readable only by the user
fi

# Load environment variables
eval "$(load_env_vars)"

# Validate environment variables
if ! validate_env_vars; then
    log_message "Error: Missing required environment variables. Please check your .env file."
    exit 1
fi

# Initialize database
if ! initialize_database; then
    exit 1
fi

# Check if port is available
if ! check_port 5000; then
    log_message "Error: Port 5000 is already in use. Please free up the port and try again."
    exit 1
fi

# Start the Flask server
log_message "Starting Flask server..."
python -m flask run --host=0.0.0.0 --port=5000 --no-reload 2>&1 | tee -a logs/server.log

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