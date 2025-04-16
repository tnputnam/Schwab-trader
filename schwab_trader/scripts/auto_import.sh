#!/bin/bash

# Set up logging
LOG_DIR="/home/thomas/schwab_trader_backups/logs"
LOG_FILE="$LOG_DIR/auto_import.log"
ERROR_LOG="$LOG_DIR/auto_import_error.log"

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

# Check if today is the 5th of the month
if [ "$(date +%d)" != "05" ]; then
    log "Not the 5th of the month, skipping import"
    exit 0
fi

# Activate virtual environment
source /home/thomas/Desktop/business/Stock\ Market\ program/venv/bin/activate

# Set up environment variables
export FLASK_APP=schwab_trader:create_app
export FLASK_ENV=development

# Create backup directory for portfolio files
BACKUP_DIR="/home/thomas/schwab_trader_backups/portfolio"
mkdir -p "$BACKUP_DIR"

# Generate filename with current date
DATE=$(date +%Y%m%d)
PORTFOLIO_FILE="$BACKUP_DIR/portfolio_$DATE.csv"

# Download portfolio from Schwab (you'll need to implement this part)
# For now, we'll assume the file is manually placed in the backup directory
if [ ! -f "$PORTFOLIO_FILE" ]; then
    log_error "Portfolio file not found: $PORTFOLIO_FILE"
    exit 1
fi

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