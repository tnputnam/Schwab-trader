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
from . import root, news, strategies, compare, portfolio, analysis, alerts, watchlist, analysis_dashboard
from .auth import bp as auth_bp
from .root import root_bp
from .analysis import analysis_bp
from .trading import trading_bp
from .portfolio import portfolio_bp

__all__ = ['root', 'news', 'strategies', 'compare', 'portfolio', 'analysis', 'alerts', 'watchlist', 'auth_bp', 'analysis_dashboard']

def init_app(app):
    """Initialize routes for the application."""
    app.register_blueprint(root_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analysis_dashboard.analysis_dashboard_bp, url_prefix='/analysis/dashboard') 