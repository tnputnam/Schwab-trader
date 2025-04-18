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

# Main script
log_message "Starting server restart process..."

# Kill any existing Flask server
kill_flask_server

# Set environment variables
export FLASK_APP=schwab_trader
export FLASK_DEBUG=1

# Start the Flask server
log_message "Starting Flask server..."
flask run --host=0.0.0.0 --port=5000 