"""Logging service for the application."""
import logging
import os
from datetime import datetime

class LoggingService:
    def __init__(self, name='app'):
        """Initialize the logging service."""
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')

        # File handler
        file_handler = logging.FileHandler(
            f'logs/{name}_{datetime.now().strftime("%Y%m%d")}.log'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message):
        """Log an info message."""
        self.logger.info(message)

    def error(self, message):
        """Log an error message."""
        self.logger.error(message)

    def warning(self, message):
        """Log a warning message."""
        self.logger.warning(message)

    def debug(self, message):
        """Log a debug message."""
        self.logger.debug(message) 