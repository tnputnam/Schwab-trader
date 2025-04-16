"""Configuration settings for Schwab Trader."""
import os
from dotenv import load_dotenv

load_dotenv()

# Get the absolute path to the instance directory
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, '..', 'instance')
DB_PATH = os.path.join(INSTANCE_DIR, 'schwab_trader.db')

class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    
    # SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
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

class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
