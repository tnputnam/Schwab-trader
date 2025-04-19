#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages with timestamps
log_message() {
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1"
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

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        log_message "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    log_message "Activating virtual environment..."
    source venv/bin/activate
    
    log_message "Installing/updating dependencies..."
    pip install -r requirements.txt
}

# Function to load environment variables
load_env() {
    local env_file=$1
    if [ -f "$env_file" ]; then
        log_message "Loading environment variables from $env_file..."
        export $(grep -v '^#' "$env_file" | xargs)
    else
        log_message "Warning: $env_file not found. Using default environment variables."
    fi
}

# Main script
main() {
    # Check for required commands
    for cmd in python3 pip virtualenv; do
        if ! command_exists $cmd; then
            log_message "Error: $cmd is required but not installed."
            exit 1
        fi
    done
    
    # Check disk space
    if ! check_disk_space; then
        exit 1
    fi
    
    # Kill existing Flask server
    kill_flask_server
    
    # Setup virtual environment
    setup_venv
    
    # Load environment variables
    if [ "$1" == "test" ]; then
        load_env "schwab_trader/.env.test"
    else
        load_env ".env"
    fi
    
    # Start Flask application
    log_message "Starting Flask application..."
    export FLASK_APP=auth_app.py
    export FLASK_ENV=development
    
    if [ "$1" == "test" ]; then
        python -m flask run --host=0.0.0.0 --port=5001
    else
        python -m flask run --host=0.0.0.0 --port=5000
    fi
}

# Run main function with arguments
main "$@" 