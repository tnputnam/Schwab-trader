import os
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import time
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/git_monitor_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class GitMonitor:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path)
        self.status_file = self.repo_path / "git_status_history.json"
        self.status_history = self.load_status_history()
        
    def load_status_history(self) -> dict:
        """Load previous git status history."""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {'history': []}
        return {'history': []}
    
    def save_status_history(self):
        """Save current git status history."""
        with open(self.status_file, 'w') as f:
            json.dump(self.status_history, f, indent=2)
    
    def get_git_status(self) -> dict:
        """Get current git status."""
        try:
            # Get status
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # Get branch info
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # Get last commit info
            commit_result = subprocess.run(
                ['git', 'log', '-1', '--pretty=format:%H %s %ad', '--date=iso'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            
            # Parse status output
            status_lines = status_result.stdout.strip().split('\n')
            changes = {
                'modified': [],
                'added': [],
                'deleted': [],
                'untracked': []
            }
            
            for line in status_lines:
                if line:
                    status = line[:2].strip()
                    filename = line[3:]
                    if status == 'M':
                        changes['modified'].append(filename)
                    elif status == 'A':
                        changes['added'].append(filename)
                    elif status == 'D':
                        changes['deleted'].append(filename)
                    elif status == '??':
                        changes['untracked'].append(filename)
            
            # Parse commit info
            commit_info = {}
            if commit_result.stdout:
                commit_parts = commit_result.stdout.split(' ', 2)
                if len(commit_parts) == 3:
                    commit_info = {
                        'hash': commit_parts[0],
                        'message': commit_parts[1],
                        'date': commit_parts[2]
                    }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'branch': branch_result.stdout.strip(),
                'changes': changes,
                'last_commit': commit_info
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error getting git status: {str(e)}")
            return None
    
    def check_for_updates(self, interval: int = 300):
        """Monitor git status at regular intervals."""
        logger.info(f"Starting git status monitoring (checking every {interval} seconds)")
        
        while True:
            try:
                current_status = self.get_git_status()
                if current_status:
                    # Add to history
                    self.status_history['history'].append(current_status)
                    self.save_status_history()
                    
                    # Log changes
                    changes = current_status['changes']
                    if any(changes.values()):
                        logger.info("\nGit Status Update:")
                        logger.info(f"Branch: {current_status['branch']}")
                        logger.info(f"Modified files: {len(changes['modified'])}")
                        logger.info(f"Added files: {len(changes['added'])}")
                        logger.info(f"Deleted files: {len(changes['deleted'])}")
                        logger.info(f"Untracked files: {len(changes['untracked'])}")
                        
                        if current_status['last_commit']:
                            logger.info(f"Last commit: {current_status['last_commit']['message']}")
                            logger.info(f"Commit date: {current_status['last_commit']['date']}")
                    else:
                        logger.info("No changes detected")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"Error during monitoring: {str(e)}")
                time.sleep(interval)
    
    def generate_status_report(self) -> dict:
        """Generate a summary report of git status history."""
        if not self.status_history['history']:
            return {'message': 'No history available'}
        
        # Get the most recent status
        latest_status = self.status_history['history'][-1]
        
        # Calculate statistics
        total_changes = sum(len(files) for files in latest_status['changes'].values())
        days_since_last_commit = 0
        if latest_status['last_commit']:
            last_commit_date = datetime.fromisoformat(latest_status['last_commit']['date'])
            days_since_last_commit = (datetime.now() - last_commit_date).days
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_branch': latest_status['branch'],
            'total_changes': total_changes,
            'days_since_last_commit': days_since_last_commit,
            'file_changes': latest_status['changes'],
            'last_commit': latest_status['last_commit']
        }

if __name__ == '__main__':
    monitor = GitMonitor()
    monitor.check_for_updates() 