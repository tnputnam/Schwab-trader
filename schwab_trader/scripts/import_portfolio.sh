#!/bin/bash

# Set up logging
LOG_DIR="/home/thomas/schwab_trader_backups/logs"
LOG_FILE="$LOG_DIR/portfolio_import.log"
ERROR_LOG="$LOG_DIR/portfolio_import_error.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"
touch "$LOG_FILE" "$ERROR_LOG"

# Logging functions
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1" | tee -a "$ERROR_LOG"
}

# Check if file path is provided
if [ -z "$1" ]; then
    echo "Usage: ./import_portfolio.sh <path_to_portfolio_csv>"
    exit 1
fi

PORTFOLIO_FILE="$1"

# Validate file exists
if [ ! -f "$PORTFOLIO_FILE" ]; then
    log_error "Portfolio file not found: $PORTFOLIO_FILE"
    exit 1
fi

# Activate virtual environment
source /home/thomas/Desktop/business/Stock\ Market\ program/venv/bin/activate

# Set up environment variables
export FLASK_APP=schwab_trader:create_app
export FLASK_ENV=development

# Create backup directory for portfolio files
BACKUP_DIR="/home/thomas/schwab_trader_backups/portfolio"
mkdir -p "$BACKUP_DIR"

# Create a backup of the file with timestamp
BACKUP_FILE="$BACKUP_DIR/portfolio_$(date +%Y%m%d_%H%M%S).csv"
cp "$PORTFOLIO_FILE" "$BACKUP_FILE"
log "Created backup at: $BACKUP_FILE"

# Run the import script
log "Starting portfolio import"
python /home/thomas/Desktop/business/Stock\ Market\ program/schwab_trader/scripts/auto_import.py "$PORTFOLIO_FILE"

if [ $? -eq 0 ]; then
    log "Portfolio import completed successfully"
else
    log_error "Portfolio import failed"
    exit 1
fi

# Clean up old backup files (keep last 12 months)
find "$BACKUP_DIR" -name "portfolio_*.csv" -mtime +365 -delete
log "Cleaned up old backup files" 