#!/usr/bin/env python3
import os
import shutil
import datetime
import json
import subprocess
from pathlib import Path
import glob

# Configuration
PROJECT_ROOT = Path('/home/thomas/Desktop/business/Stock Market program')
BACKUP_ROOT = Path.home() / 'schwab_trader_backups'  # Changed to home directory
CURSOR_SETTINGS = Path.home() / '.cursor'  # Cursor settings directory
MAX_BACKUPS = 4  # Keep only the last 4 backups

def ensure_directory_exists(path):
    """Ensure the directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)

def get_backup_name():
    """Generate a backup name with timestamp."""
    return datetime.datetime.now().strftime('backup_%Y%m%d_%H%M%S')

def cleanup_old_backups():
    """Remove old backups, keeping only the last MAX_BACKUPS."""
    backup_dirs = sorted(glob.glob(str(BACKUP_ROOT / 'backup_*')))
    if len(backup_dirs) > MAX_BACKUPS:
        for old_backup in backup_dirs[:-MAX_BACKUPS]:
            shutil.rmtree(old_backup)
            print(f"Removed old backup: {old_backup}")

def backup_cursor_settings(backup_dir):
    """Backup Cursor settings."""
    cursor_backup_dir = backup_dir / 'cursor_settings'
    ensure_directory_exists(cursor_backup_dir)
    
    if CURSOR_SETTINGS.exists():
        # Copy Cursor settings
        for item in CURSOR_SETTINGS.iterdir():
            if item.is_file():
                shutil.copy2(item, cursor_backup_dir / item.name)
            elif item.is_dir():
                shutil.copytree(item, cursor_backup_dir / item.name, dirs_exist_ok=True)
        
        print(f"Backed up Cursor settings to {cursor_backup_dir}")

def backup_project_files(backup_dir):
    """Backup project files."""
    project_backup_dir = backup_dir / 'project_files'
    ensure_directory_exists(project_backup_dir)
    
    # Files and directories to exclude from backup
    exclude = {
        '__pycache__',
        '.git',
        '.gitignore',
        'venv',
        'logs',
        '.pytest_cache',
        '.coverage',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.DS_Store'
    }
    
    # Copy project files
    for item in PROJECT_ROOT.iterdir():
        if item.name in exclude:
            continue
        if item.is_file():
            shutil.copy2(item, project_backup_dir / item.name)
        elif item.is_dir():
            shutil.copytree(item, project_backup_dir / item.name, 
                          ignore=shutil.ignore_patterns(*exclude),
                          dirs_exist_ok=True)
    
    print(f"Backed up project files to {project_backup_dir}")

def create_backup_info(backup_dir):
    """Create a backup info file with metadata."""
    info = {
        'timestamp': datetime.datetime.now().isoformat(),
        'project_root': str(PROJECT_ROOT),
        'backup_location': str(backup_dir),
        'cursor_settings': str(CURSOR_SETTINGS),
        'system_info': {
            'python_version': subprocess.check_output(['python', '--version']).decode().strip(),
            'django_version': subprocess.check_output(['python', '-m', 'pip', 'show', 'django']).decode().strip(),
        }
    }
    
    with open(backup_dir / 'backup_info.json', 'w') as f:
        json.dump(info, f, indent=4)

def main():
    """Main backup function."""
    try:
        # Create backup directory with timestamp
        backup_name = get_backup_name()
        backup_dir = BACKUP_ROOT / backup_name
        ensure_directory_exists(backup_dir)
        
        print(f"Starting backup: {backup_name}")
        
        # Backup Cursor settings
        backup_cursor_settings(backup_dir)
        
        # Backup project files
        backup_project_files(backup_dir)
        
        # Create backup info
        create_backup_info(backup_dir)
        
        # Cleanup old backups
        cleanup_old_backups()
        
        print(f"Backup completed successfully: {backup_dir}")
        
    except Exception as e:
        print(f"Backup failed: {str(e)}")
        raise

if __name__ == '__main__':
    main() 