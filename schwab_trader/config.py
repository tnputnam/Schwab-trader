import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///schwab_trader.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cache configuration
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')  # Use 'redis' in production, 'simple' for testing
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Redis configuration (only used if CACHE_TYPE is 'redis')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CACHE_REDIS_URL = REDIS_URL
