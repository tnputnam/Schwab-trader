#!/bin/bash

# Default ports
DEFAULT_PROD_PORT=5000
DEFAULT_TEST_PORT=5001

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
        log_message "Port $port is already in use"
        return 1
    fi
    return 0
}

# Function to find an available port
find_available_port() {
    local start_port=$1
    local max_port=$2
    local port=$start_port
    
    while [ $port -le $max_port ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    
    log_message "Error: Could not find an available port between $start_port and $max_port"
    return 1
}

# Function to check disk space
check_disk_space() {
    local required_space=1000  # 1GB in MB
    local available_space=$(df -m . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt "$required_space" ]; then
        log_message "Warning: Low disk space. Available: ${available_space}MB, Required: ${required_space}MB"
        return 1
    fi
    return 0
}

# Function to load environment variables
load_env() {
    if [ -f ".env" ]; then
        log_message "Loading environment variables from .env"
        export $(grep -v '^#' .env | xargs)
    else
        log_message "Error: .env file not found"
        return 1
    fi
}

# Function to start the application
start_application() {
    local port=$1
    local env=$2
    
    log_message "Starting application in $env mode on port $port"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    else
        log_message "Error: Virtual environment not found"
        return 1
    fi
    
    # Load environment variables
    if ! load_env; then
        return 1
    fi
    
    # Set Flask environment variables
    export FLASK_APP=auth_app.py
    export FLASK_ENV=development
    export FLASK_DEBUG=1
    
    # Start the application using wsgi.py
    python wsgi.py &
    
    # Store the process ID
    echo $! > .flask.pid
    
    log_message "Application started with PID $(cat .flask.pid)"
}

# Main script
main() {
    # Check if running in test mode
    if [ "$1" == "--test" ]; then
        ENV="test"
        PORT=$(find_available_port $DEFAULT_TEST_PORT $((DEFAULT_TEST_PORT + 10)))
    else
        ENV="production"
        PORT=$(find_available_port $DEFAULT_PROD_PORT $((DEFAULT_PROD_PORT + 10)))
    fi
    
    if [ -z "$PORT" ]; then
        log_message "Error: Could not start application - no available ports"
        exit 1
    fi
    
    # Check disk space
    if ! check_disk_space; then
        log_message "Warning: Starting application with low disk space"
    fi
    
    # Start the application
    start_application $PORT $ENV
    
    if [ $? -eq 0 ]; then
        log_message "Application started successfully"
        log_message "Access the application at: http://localhost:$PORT"
    else
        log_message "Error: Failed to start application"
        exit 1
    fi
}

# Run the main function
main "$@" 