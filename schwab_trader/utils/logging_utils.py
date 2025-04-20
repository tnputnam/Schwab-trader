"""Centralized logging management for Schwab Trader."""
import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional
from .config_utils import Config

def setup_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """Set up a logger with the specified name and level."""
    # Create logs directory if it doesn't exist
    os.makedirs(Config.LOG_DIR, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    
    # Set log level
    level = level or Config.LOG_LEVEL
    logger.setLevel(getattr(logging, level.upper()))
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Create file handler
    log_file = os.path.join(Config.LOG_DIR, f'{name}.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(file_formatter)
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create default logger
logger = setup_logger('schwab_trader')

def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Set up file handler
        file_handler = RotatingFileHandler(
            'logs/app.log',
            maxBytes=1024 * 1024,  # 1MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Set up console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        
        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        # Set log level
        logger.setLevel(logging.INFO)
    
    return logger 