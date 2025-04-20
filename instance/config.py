"""
Application configuration.
"""

import os

# Flask configuration
SECRET_KEY = 'dev'
SQLALCHEMY_DATABASE_URI = 'sqlite:///schwab_trader.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Cache configuration
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300
CACHE_THRESHOLD = 1000
CACHE_OPTIONS = {
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 1000
}

# Schwab API configuration
SCHWAB_API_KEY = os.environ.get('SCHWAB_API_KEY', '')
SCHWAB_API_SECRET = os.environ.get('SCHWAB_API_SECRET', '')
SCHWAB_API_ENDPOINT = os.environ.get('SCHWAB_API_ENDPOINT', 'https://api.schwabapi.com')

# Application settings
DEBUG = True
TESTING = False

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///schwab_trader.db')

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'NXFO...L4G1')

# Schwab API configuration
SCHWAB_CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID', 'nuXZreDmdJzAsb4XGU24pArjpkJPltXB')
SCHWAB_CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET', 'xzuIIEWzAs7nQd5A')
SCHWAB_REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI', 'https://a3a3-2605-59c8-7260-b910-fc7e-29c-c724-b4a1.ngrok-free.app/auth/callback')
SCHWAB_AUTH_URL = os.getenv('SCHWAB_AUTH_URL', 'https://api.schwabapi.com/v1/oauth/authorize')
SCHWAB_TOKEN_URL = os.getenv('SCHWAB_TOKEN_URL', 'https://api.schwabapi.com/v1/oauth/token')
SCHWAB_SCOPES = os.getenv('SCHWAB_SCOPES', 'read_accounts trade read_positions')
SCHWAB_API_BASE_URL = os.getenv('SCHWAB_API_BASE_URL', 'https://api.schwabapi.com/v1')

# Flask configuration
ENV = os.getenv('FLASK_ENV', 'development')

# Flask configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'
ENV = os.getenv('FLASK_ENV', 'development')

# Cache configuration
CACHE_TYPE = 'simple'
CACHE_DEFAULT_TIMEOUT = 300
CACHE_THRESHOLD = 1000
CACHE_OPTIONS = {
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_THRESHOLD': 1000
} 