#!/bin/bash

# Set up logging
LOG_DIR="/home/thomas/schwab_trader_backups/logs"
LOG_FILE="$LOG_DIR/portfolio_scraper.log"
ERROR_LOG="$LOG_DIR/portfolio_scraper_error.log"

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

# Activate virtual environment
source /home/thomas/Desktop/business/Stock\ Market\ program/venv/bin/activate

# Set up environment variables
export FLASK_APP=schwab_trader:create_app
export FLASK_ENV=development

# Run the scraper
log "Starting portfolio scraper"
python /home/thomas/Desktop/business/Stock\ Market\ program/schwab_trader/scripts/portfolio_scraper.py

if [ $? -eq 0 ]; then
    log "Portfolio scraping completed successfully"
else
    log_error "Portfolio scraping failed"
    exit 1
fi 