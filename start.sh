#!/bin/bash

# Default ports
DEFAULT_PROD_PORT=5000
DEFAULT_TEST_PORT=5001
DEFAULT_DEV_PORT=5002

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to log messages with timestamps
log_message() {
    local level=${2:-"INFO"}
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $1"
}

# Function to check if a port is available
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        log_message "Port $port is already in use" "WARNING"
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
    
    log_message "Error: Could not find an available port between $start_port and $max_port" "ERROR"
    return 1
}

# Function to check disk space
check_disk_space() {
    local required_space=1000  # 1GB in MB
    local available_space=$(df -m . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt "$required_space" ]; then
        log_message "Warning: Low disk space. Available: ${available_space}MB, Required: ${required_space}MB" "WARNING"
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
        log_message "Error: .env file not found" "ERROR"
        return 1
    fi
}

# Function to install the package in development mode
install_package() {
    log_message "Installing package in development mode..."
    if [ -f "setup.py" ]; then
        pip install -e .
        if [ $? -ne 0 ]; then
            log_message "Error: Failed to install package in development mode" "ERROR"
            return 1
        fi
        log_message "Package installed successfully"
    else
        log_message "Error: setup.py not found" "ERROR"
        return 1
    fi
}

# Function to check if application is running
is_application_running() {
    local port=$1
    if lsof -i :$port > /dev/null; then
        return 0
    fi
    return 1
}

# Function to stop the application
stop_application() {
    local port=$1
    log_message "Stopping application on port $port..."
    
    # Find and kill processes using the port
    local pids=$(lsof -ti :$port)
    if [ ! -z "$pids" ]; then
        for pid in $pids; do
            kill $pid 2>/dev/null || kill -9 $pid 2>/dev/null
        done
        log_message "Application stopped successfully"
    else
        log_message "No application running on port $port" "WARNING"
    fi
}

# Function to start the application
start_application() {
    local env_mode=$1
    local port=$2
    
    # Check if application is already running
    if is_application_running $port; then
        log_message "Application is already running on port $port" "WARNING"
        read -p "Do you want to stop it and start a new instance? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_application $port
        else
            log_message "Aborting start" "INFO"
            return 1
        fi
    fi
    
    log_message "Starting application in $env_mode mode on port $port..."
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    elif [ -d "schwab-trading-env" ]; then
        source schwab-trading-env/bin/activate
    else
        log_message "Error: Virtual environment not found" "ERROR"
        return 1
    fi
    
    # Load environment variables
    if ! load_env; then
        log_message "Warning: Proceeding without environment variables" "WARNING"
    fi
    
    # Install package in development mode
    install_package
    
    # Set Flask environment variables
    export FLASK_APP=wsgi.py
    export FLASK_ENV=$env_mode
    export FLASK_DEBUG=1
    
    # Start the application
    if [ "$env_mode" == "development" ]; then
        flask run --port=$port
    else
        gunicorn --bind 0.0.0.0:$port wsgi:app
    fi
}

# Function to display help
show_help() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  --dev     Start in development mode"
    echo "  --test    Start in test mode"
    echo "  --prod    Start in production mode (default)"
    echo "  --stop    Stop the application"
    echo "  --help    Show this help message"
}

# Main script
main() {
    # Parse command line arguments
    case "$1" in
        --dev)
            ENV="development"
            PORT=$(find_available_port $DEFAULT_DEV_PORT $((DEFAULT_DEV_PORT + 10)))
            ;;
        --test)
            ENV="test"
            PORT=$(find_available_port $DEFAULT_TEST_PORT $((DEFAULT_TEST_PORT + 10)))
            ;;
        --prod)
            ENV="production"
            PORT=$(find_available_port $DEFAULT_PROD_PORT $((DEFAULT_PROD_PORT + 10)))
            ;;
        --stop)
            if [ -z "$2" ]; then
                log_message "Error: Port number required for --stop option" "ERROR"
                exit 1
            fi
            stop_application $2
            exit 0
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            ENV="production"
            PORT=$(find_available_port $DEFAULT_PROD_PORT $((DEFAULT_PROD_PORT + 10)))
            ;;
    esac
    
    if [ -z "$PORT" ]; then
        log_message "Error: Could not start application - no available ports" "ERROR"
        exit 1
    fi
    
    # Check disk space
    if ! check_disk_space; then
        log_message "Warning: Starting application with low disk space" "WARNING"
    fi
    
    # Start the application
    start_application $ENV $PORT
    
    if [ $? -eq 0 ]; then
        log_message "Application started successfully"
        log_message "Access the application at: http://localhost:$PORT"
    else
        log_message "Error: Failed to start application" "ERROR"
        exit 1
    fi
}

# Run the main function
main "$@" 