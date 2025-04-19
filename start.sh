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
        log_message "Error: Insufficient disk space. Required: ${required_space}MB, Available: ${available_space}MB"
        return 1
    fi
    return 0
}

# Function to kill existing Flask server
kill_flask_server() {
    local port=$1
    log_message "Checking for existing Flask server on port $port..."
    if pgrep -f "python -m flask.*:$port" > /dev/null; then
        log_message "Stopping existing Flask server on port $port..."
        pkill -f "python -m flask.*:$port"
        sleep 2  # Give it time to shut down gracefully
        
        # Double check if port is still in use
        if ! check_port $port; then
            log_message "Force closing port $port..."
            kill $(lsof -t -i:$port) 2>/dev/null || true
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
    for cmd in python3 pip; do
        if ! command_exists $cmd; then
            log_message "Error: $cmd is required but not installed."
            exit 1
        fi
    done
    
    # Check if python3-venv is installed
    if ! python3 -c "import venv" 2>/dev/null; then
        log_message "Error: python3-venv is required but not installed."
        log_message "Please install it with: sudo apt-get install python3-venv"
        exit 1
    fi
    
    # Check disk space
    if ! check_disk_space; then
        exit 1
    fi
    
    # Determine environment and port
    local is_test=false
    local port=$DEFAULT_PROD_PORT
    
    if [ "$1" == "test" ]; then
        is_test=true
        port=$DEFAULT_TEST_PORT
    fi
    
    # Find available port if default is in use
    if ! check_port $port; then
        log_message "Default port $port is in use, searching for alternative..."
        if [ "$is_test" = true ]; then
            port=$(find_available_port $DEFAULT_TEST_PORT $((DEFAULT_TEST_PORT + 10)))
        else
            port=$(find_available_port $DEFAULT_PROD_PORT $((DEFAULT_PROD_PORT + 10)))
        fi
        if [ $? -ne 0 ]; then
            exit 1
        fi
        log_message "Using alternative port $port"
    fi
    
    # Kill existing Flask server on the port
    kill_flask_server $port
    
    # Setup virtual environment
    setup_venv
    
    # Load environment variables
    if [ "$is_test" = true ]; then
        load_env "schwab_trader/.env.test"
    else
        load_env ".env"
    fi
    
    # Start Flask application
    log_message "Starting Flask application on port $port..."
    export FLASK_APP=auth_app.py
    export FLASK_ENV=development
    
    # Update callback URL in environment if it's test mode
    if [ "$is_test" = true ]; then
        export SCHWAB_REDIRECT_URI="http://localhost:$port/auth/callback"
        log_message "Updated callback URL to: $SCHWAB_REDIRECT_URI"
    fi
    
    python -m flask run --host=0.0.0.0 --port=$port
}

# Run main function with arguments
main "$@" 