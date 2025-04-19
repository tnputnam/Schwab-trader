"""Centralized logging service with GUI display capabilities."""
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional
from collections import deque
import os

class LoggingService:
    def __init__(self, max_logs: int = 1000):
        self.max_logs = max_logs
        self.log_buffer = deque(maxlen=max_logs)
        self.log_levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        
        # Configure file logging
        self.setup_file_logging()
        
        # Initialize logger
        self.logger = logging.getLogger('schwab_trader')
        self.logger.setLevel(logging.DEBUG)
        
    def setup_file_logging(self):
        """Setup file logging with rotation."""
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create handlers
        file_handler = logging.FileHandler(
            f'{log_dir}/schwab_trader_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Add handlers to root logger
        logging.getLogger().addHandler(file_handler)
        
    def log(self, level: str, message: str, context: Optional[Dict] = None):
        """Log a message with context and store in buffer for GUI display."""
        if level not in self.log_levels:
            self.logger.warning(f"Invalid log level: {level}")
            return
            
        # Create log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'context': context or {}
        }
        
        # Add to buffer
        self.log_buffer.append(log_entry)
        
        # Log to file
        if context:
            self.logger.log(self.log_levels[level], f"{message} | Context: {json.dumps(context)}")
        else:
            self.logger.log(self.log_levels[level], message)
            
    def get_recent_logs(self, level: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get recent logs, optionally filtered by level."""
        logs = list(self.log_buffer)
        if level:
            logs = [log for log in logs if log['level'] == level]
        return logs[-limit:]
        
    def get_log_stats(self) -> Dict:
        """Get statistics about the logs."""
        logs = list(self.log_buffer)
        return {
            'total_logs': len(logs),
            'levels': {
                level: len([log for log in logs if log['level'] == level])
                for level in self.log_levels.keys()
            },
            'last_error': next(
                (log for log in reversed(logs) if log['level'] in ['ERROR', 'CRITICAL']),
                None
            )
        }
        
    def clear_logs(self):
        """Clear the log buffer."""
        self.log_buffer.clear()
        
    def export_logs(self, filepath: str):
        """Export logs to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(list(self.log_buffer), f, indent=2)
            
    def get_log_level_color(self, level: str) -> str:
        """Get color for log level display."""
        colors = {
            'DEBUG': '#6c757d',    # Gray
            'INFO': '#0d6efd',     # Blue
            'WARNING': '#ffc107',  # Yellow
            'ERROR': '#dc3545',    # Red
            'CRITICAL': '#dc3545'  # Red
        }
        return colors.get(level, '#6c757d') 