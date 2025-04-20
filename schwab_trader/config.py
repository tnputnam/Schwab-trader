"""Configuration settings for Schwab Trader."""
import os
from dotenv import load_dotenv
from pathlib import Path
from schwab_trader.utils.logger import setup_logger
from typing import Dict, Any, Optional, List, Union
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger('config')

class Config:
    # Base configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///data/schwab_trader.db')
    
    # Flask-Login configuration
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    
    # Session configuration
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_FILE_DIR = os.getenv('SESSION_FILE_DIR', 'sessions')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'true').lower() == 'true'
    PERMANENT_SESSION_LIFETIME = int(os.getenv('PERMANENT_SESSION_LIFETIME', '3600'))
    
    # API configuration
    SCHWAB_API_KEY = os.getenv('SCHWAB_API_KEY')
    SCHWAB_API_SECRET = os.getenv('SCHWAB_API_SECRET')
    SCHWAB_API_BASE_URL = os.getenv('SCHWAB_API_BASE_URL', 'https://api.schwab.com')
    SCHWAB_REDIRECT_URL = os.getenv('SCHWAB_REDIRECT_URL', 'http://localhost:5000/auth/callback')
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Cache configuration
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))
    
    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', '200 per day')
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')
    
    # News service configuration
    NEWS_UPDATE_INTERVAL = int(os.getenv('NEWS_UPDATE_INTERVAL', '300'))  # 5 minutes
    NEWS_MAX_ARTICLES = int(os.getenv('NEWS_MAX_ARTICLES', '100'))
    NEWS_SOURCES = json.loads(os.getenv('NEWS_SOURCES', '["reuters", "bloomberg", "cnbc"]'))
    
    # Analysis configuration
    ANALYSIS_HISTORICAL_DAYS = int(os.getenv('ANALYSIS_HISTORICAL_DAYS', '365'))
    ANALYSIS_VOLUME_WINDOW = int(os.getenv('ANALYSIS_VOLUME_WINDOW', '20'))
    ANALYSIS_RSI_PERIOD = int(os.getenv('ANALYSIS_RSI_PERIOD', '14'))
    ANALYSIS_MACD_FAST = int(os.getenv('ANALYSIS_MACD_FAST', '12'))
    ANALYSIS_MACD_SLOW = int(os.getenv('ANALYSIS_MACD_SLOW', '26'))
    ANALYSIS_MACD_SIGNAL = int(os.getenv('ANALYSIS_MACD_SIGNAL', '9'))
    
    # Real-time data configuration
    REALTIME_UPDATE_INTERVAL = int(os.getenv('REALTIME_UPDATE_INTERVAL', '5'))  # seconds
    REALTIME_MAX_RETRIES = int(os.getenv('REALTIME_MAX_RETRIES', '3'))
    REALTIME_RETRY_DELAY = int(os.getenv('REALTIME_RETRY_DELAY', '5'))  # seconds
    
    # Strategy testing configuration
    STRATEGY_TEST_START_DATE = os.getenv('STRATEGY_TEST_START_DATE', '2020-01-01')
    STRATEGY_TEST_END_DATE = os.getenv('STRATEGY_TEST_END_DATE', '2023-12-31')
    STRATEGY_TEST_INITIAL_CAPITAL = float(os.getenv('STRATEGY_TEST_INITIAL_CAPITAL', '100000'))
    STRATEGY_TEST_COMMISSION = float(os.getenv('STRATEGY_TEST_COMMISSION', '0.01'))
    
    # Enhanced validation rules
    VALIDATION_RULES = {
        'NEWS_UPDATE_INTERVAL': {'min': 60, 'max': 3600},
        'ANALYSIS_HISTORICAL_DAYS': {'min': 30, 'max': 3650},
        'REALTIME_UPDATE_INTERVAL': {'min': 1, 'max': 60},
        'STRATEGY_TEST_INITIAL_CAPITAL': {'min': 1000, 'max': 1000000},
        'STRATEGY_TEST_COMMISSION': {'min': 0, 'max': 0.1},
        'ANALYSIS_VOLUME_WINDOW': {'min': 5, 'max': 100},
        'ANALYSIS_RSI_PERIOD': {'min': 2, 'max': 30},
        'ANALYSIS_MACD_FAST': {'min': 2, 'max': 50},
        'ANALYSIS_MACD_SLOW': {'min': 5, 'max': 100},
        'ANALYSIS_MACD_SIGNAL': {'min': 2, 'max': 30},
        'NEWS_MAX_ARTICLES': {'min': 10, 'max': 1000},
        'REALTIME_MAX_RETRIES': {'min': 1, 'max': 10},
        'REALTIME_RETRY_DELAY': {'min': 1, 'max': 60}
    }

    # Format validation rules
    FORMAT_RULES = {
        'STRATEGY_TEST_START_DATE': {'format': '%Y-%m-%d', 'type': 'date'},
        'STRATEGY_TEST_END_DATE': {'format': '%Y-%m-%d', 'type': 'date'},
        'NEWS_SOURCES': {'type': 'json_array'},
        'SCHWAB_API_BASE_URL': {'type': 'url'}
    }

    @classmethod
    def validate_format(cls, key: str, value: Any) -> Optional[str]:
        """Validate format of configuration values."""
        if key not in cls.FORMAT_RULES:
            return None

        rule = cls.FORMAT_RULES[key]
        if rule['type'] == 'date':
            try:
                datetime.strptime(value, rule['format'])
            except ValueError:
                return f"Invalid date format for {key}. Expected format: {rule['format']}"
        elif rule['type'] == 'json_array':
            try:
                if not isinstance(json.loads(value), list):
                    return f"{key} must be a JSON array"
            except json.JSONDecodeError:
                return f"Invalid JSON format for {key}"
        elif rule['type'] == 'url':
            if not value.startswith(('http://', 'https://')):
                return f"Invalid URL format for {key}"

        return None

    @classmethod
    def validate_config(cls) -> Dict[str, List[str]]:
        """Validate configuration values against defined rules."""
        errors: Dict[str, List[str]] = {}
        
        # Validate numeric ranges
        for key, rules in cls.VALIDATION_RULES.items():
            value = getattr(cls, key, None)
            if value is not None:
                if 'min' in rules and value < rules['min']:
                    errors.setdefault(key, []).append(
                        f"Value {value} is below minimum {rules['min']}"
                    )
                if 'max' in rules and value > rules['max']:
                    errors.setdefault(key, []).append(
                        f"Value {value} is above maximum {rules['max']}"
                    )

        # Validate formats
        for key in cls.FORMAT_RULES:
            value = getattr(cls, key, None)
            if value is not None:
                format_error = cls.validate_format(key, value)
                if format_error:
                    errors.setdefault(key, []).append(format_error)

        # Validate dependencies
        if cls.STRATEGY_TEST_START_DATE and cls.STRATEGY_TEST_END_DATE:
            start = datetime.strptime(cls.STRATEGY_TEST_START_DATE, '%Y-%m-%d')
            end = datetime.strptime(cls.STRATEGY_TEST_END_DATE, '%Y-%m-%d')
            if start >= end:
                errors.setdefault('STRATEGY_TEST_DATES', []).append(
                    "Start date must be before end date"
                )

        return errors

    @classmethod
    def init_app(cls, app):
        # Create necessary directories
        for directory in [cls.LOG_DIR, cls.SESSION_FILE_DIR, 'data']:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        app.logger.setLevel(cls.LOG_LEVEL)
        
        # Load environment variables
        load_dotenv()
        
        # Validate configuration
        errors = cls.validate_config()
        if errors:
            logger.warning("Configuration validation errors found:")
            for key, error_list in errors.items():
                for error in error_list:
                    logger.warning(f"{key}: {error}")

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    
    # Development-specific overrides
    NEWS_UPDATE_INTERVAL = 60  # 1 minute for faster testing
    REALTIME_UPDATE_INTERVAL = 2  # 2 seconds for faster testing

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Testing-specific overrides
    NEWS_UPDATE_INTERVAL = 30  # 30 seconds for testing
    REALTIME_UPDATE_INTERVAL = 1  # 1 second for testing

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Configure file logging
        file_handler = RotatingFileHandler(
            os.path.join(cls.LOG_DIR, 'schwab_trader.log'),
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(cls.LOG_LEVEL)

class TestConfig(Config):
    """Test configuration class."""
    TESTING = True
    DATABASE_URL = 'sqlite:///test_schwab_trader.db'
    LOG_LEVEL = 'DEBUG'

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Get the appropriate configuration class based on environment."""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    return config.get(config_name, config['default'])






