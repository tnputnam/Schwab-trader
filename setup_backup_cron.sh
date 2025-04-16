#!/bin/bash

# Make backup script executable
chmod +x backup_project.py

# Create backup directory if it doesn't exist
BACKUP_DIR="$HOME/schwab_trader_backups"
mkdir -p "$BACKUP_DIR"

# Remove existing backup cron jobs
crontab -l | grep -v "backup_project.py" | crontab -

# Add cron job for backup every 10 minutes
(crontab -l 2>/dev/null; echo "*/10 * * * * cd $(pwd) && ./backup_project.py >> $BACKUP_DIR/backup.log 2>&1") | crontab -

echo "Backup system configured:"
echo "1. Backups every 10 minutes"
echo "2. Keeping last 4 backups"
echo "3. Backup location: $BACKUP_DIR"
echo "4. Log file: $BACKUP_DIR/backup.log" 