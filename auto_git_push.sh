#!/bin/bash

# Log directory and file
LOG_DIR="/home/thomas/schwab_trader_backups/logs"
LOG_FILE="$LOG_DIR/git_auto_push.log"
ERROR_LOG="$LOG_DIR/git_auto_push_error.log"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"
touch "$LOG_FILE" "$ERROR_LOG"
chmod 644 "$LOG_FILE" "$ERROR_LOG"

# Lockfile
LOCKFILE="/tmp/auto_git_push.lock"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error logging function
error_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1" | tee -a "$ERROR_LOG"
}

# Exit if another instance is running
if [ -f "$LOCKFILE" ]; then
    # Check if process is actually running
    if ps -p $(cat "$LOCKFILE") > /dev/null 2>&1; then
        error_log "Another instance is running"
        exit 1
    fi
    # Remove stale lockfile
    rm "$LOCKFILE"
    log "Removed stale lockfile"
fi

# Create lockfile
echo $$ > "$LOCKFILE"

# Cleanup lockfile on exit
trap "rm -f $LOCKFILE; log 'Script stopped, lockfile removed'" EXIT

# Function to check if there are changes to commit
check_changes() {
    git status --porcelain | grep -q "."
    return $?
}

# Function to create a backup branch before rewriting history
create_backup() {
    current_date=$(date +%Y%m%d_%H%M%S)
    branch_name="backup_$current_date"
    if git branch "$branch_name"; then
        log "Created backup branch: $branch_name"
    else
        error_log "Failed to create backup branch: $branch_name"
    fi
}

# Function to keep only last 4 commits
cleanup_commits() {
    log "Starting commit cleanup..."
    
    # Create a backup branch
    create_backup
    
    # Get the hash of the fifth most recent commit
    old_commit=$(git rev-list HEAD -n 5 | tail -n 1)
    
    if [ ! -z "$old_commit" ]; then
        # Soft reset to the fifth commit
        if git reset --soft $old_commit; then
            log "Reset to commit: $old_commit"
            
            # Create a new commit with all changes
            if git commit -m "Consolidated commit from auto-push $(date '+%Y-%m-%d %H:%M:%S')"; then
                log "Created consolidated commit"
                
                # Force push to remote
                if git push origin main --force; then
                    log "Force pushed consolidated commit to remote"
                else
                    error_log "Failed to force push consolidated commit"
                fi
            else
                error_log "Failed to create consolidated commit"
            fi
        else
            error_log "Failed to reset to commit: $old_commit"
        fi
    else
        log "No old commits to cleanup"
    fi
}

# Main loop
log "Starting auto-git-push service..."

while true; do
    if check_changes; then
        timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        log "Detected changes, starting commit process..."
        
        # Add all changes
        if git add .; then
            log "Added changes to staging"
            
            # Commit with timestamp
            if git commit -m "Auto-commit: $timestamp"; then
                log "Created commit with timestamp: $timestamp"
                
                # Push to remote
                if git push origin main; then
                    log "Pushed changes to remote"
                    
                    # Keep only last 4 commits
                    cleanup_commits
                else
                    error_log "Failed to push changes to remote"
                fi
            else
                error_log "Failed to create commit"
            fi
        else
            error_log "Failed to add changes to staging"
        fi
    else
        log "No changes detected"
    fi
    
    # Wait 1 hour (3600 seconds)
    log "Waiting 1 hour before next check..."
    sleep 3600
done 