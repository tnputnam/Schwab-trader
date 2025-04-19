"""Configuration settings for Schwab Trader."""
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

# Get the absolute path to the instance directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, '..', 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'schwab_trader.db')

class Config:
    """Base configuration."""
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev_key_123')
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # Flask
    SECRET_KEY = SECRET_KEY
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', f'sqlite:///{DB_PATH}')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Cache
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Flask-Login
    LOGIN_VIEW = 'auth.login'
    
    # Alpha Vantage API
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    # Portfolio Updater
    PORTFOLIO_UPDATE_INTERVAL = 5  # minutes

    # Schwab API Configuration
    SCHWAB_CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID')
    SCHWAB_CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET')
    SCHWAB_REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI')
    SCHWAB_AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
    SCHWAB_TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
    SCHWAB_API_BASE_URL = "https://api.schwabapi.com/v1"
    SCHWAB_SCOPES = ["readonly", "trade"]

class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False






