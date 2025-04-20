"""Routes package for Schwab Trader."""
import logging
from datetime import datetime
from flask import Blueprint

# Configure route-specific logger
logger = logging.getLogger('root_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Import blueprints
from . import root, news, strategies, compare, portfolio, analysis, alerts, watchlist
from .auth import auth_bp
from .api import api_bp

__all__ = [
    'auth_bp',
    'api_bp',
    'root',
    'news',
    'strategies',
    'compare',
    'portfolio',
    'analysis',
    'alerts',
    'watchlist'
]

def init_app(app):
    """Initialize routes for the application."""
    app.register_blueprint(root_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(auth_bp) 