#!/usr/bin/env python3
import os
import shutil
import datetime
import json
import subprocess
import logging
from pathlib import Path
import glob

# Configuration
PROJECT_ROOT = Path('/home/thomas/Desktop/business/Stock Market program')
BACKUP_ROOT = Path('/home/thomas/schwab_trader_backups')
CURSOR_SETTINGS = Path.home() / '.cursor'  # Cursor settings directory
MAX_BACKUPS = 4  # Keep only the last 4 backups

# Setup logging
LOG_DIR = BACKUP_ROOT / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'backup.log'),
        logging.StreamHandler()
    ]
)

def ensure_directory_exists(path):
    """Ensure the directory exists, create if it doesn't."""
    path.mkdir(parents=True, exist_ok=True)
    logging.debug(f"Ensured directory exists: {path}")

def get_backup_name():
    """Generate a backup name with timestamp."""
    return datetime.datetime.now().strftime('backup_%Y%m%d_%H%M%S')

def cleanup_old_backups():
    """Remove old backups, keeping only the last MAX_BACKUPS."""
    backup_dirs = sorted(glob.glob(str(BACKUP_ROOT / 'backup_*')))
    if len(backup_dirs) > MAX_BACKUPS:
        for old_backup in backup_dirs[:-MAX_BACKUPS]:
            try:
                shutil.rmtree(old_backup)
                logging.info(f"Removed old backup: {old_backup}")
            except Exception as e:
                logging.error(f"Failed to remove old backup {old_backup}: {str(e)}")

def backup_cursor_settings(backup_dir):
    """Backup Cursor settings."""
    cursor_backup_dir = backup_dir / 'cursor_settings'
    ensure_directory_exists(cursor_backup_dir)
    
    if CURSOR_SETTINGS.exists():
        try:
            # Copy Cursor settings
            for item in CURSOR_SETTINGS.iterdir():
                if item.is_file():
                    shutil.copy2(item, cursor_backup_dir / item.name)
                    logging.debug(f"Backed up Cursor file: {item.name}")
                elif item.is_dir():
                    shutil.copytree(item, cursor_backup_dir / item.name, dirs_exist_ok=True)
                    logging.debug(f"Backed up Cursor directory: {item.name}")
            
            logging.info(f"Successfully backed up Cursor settings to {cursor_backup_dir}")
        except Exception as e:
            logging.error(f"Failed to backup Cursor settings: {str(e)}")
    else:
        logging.warning(f"Cursor settings directory not found: {CURSOR_SETTINGS}")

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
    
    try:
        # Copy project files
        for item in PROJECT_ROOT.iterdir():
            if item.name in exclude:
                logging.debug(f"Skipping excluded item: {item.name}")
                continue
            if item.is_file():
                shutil.copy2(item, project_backup_dir / item.name)
                logging.debug(f"Backed up file: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, project_backup_dir / item.name, 
                              ignore=shutil.ignore_patterns(*exclude),
                              dirs_exist_ok=True)
                logging.debug(f"Backed up directory: {item.name}")
        
        logging.info(f"Successfully backed up project files to {project_backup_dir}")
    except Exception as e:
        logging.error(f"Failed to backup project files: {str(e)}")

def create_backup_info(backup_dir):
    """Create a backup info file with metadata."""
    try:
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
        logging.info("Created backup info file")
    except Exception as e:
        logging.error(f"Failed to create backup info: {str(e)}")

def main():
    """Main backup function."""
    try:
        logging.info("Starting backup process...")
        
        # Create backup directory with timestamp
        backup_name = get_backup_name()
        backup_dir = BACKUP_ROOT / backup_name
        ensure_directory_exists(backup_dir)
        
        logging.info(f"Created backup directory: {backup_name}")
        
        # Backup Cursor settings
        backup_cursor_settings(backup_dir)
        
        # Backup project files
        backup_project_files(backup_dir)
        
        # Create backup info
        create_backup_info(backup_dir)
        
        # Cleanup old backups
        cleanup_old_backups()
        
        logging.info(f"Backup completed successfully: {backup_dir}")
        
    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        raise

if __name__ == '__main__':
    main() 