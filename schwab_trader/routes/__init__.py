"""Routes package for Schwab Trader."""
import logging
from datetime import datetime

# Configure route-specific logger
logger = logging.getLogger('root_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Import blueprints
from . import root, news, strategies, compare, portfolio, analysis, alerts, watchlist
from .dashboard import bp as dashboard
from .auth import bp as auth

__all__ = ['root', 'news', 'strategies', 'compare', 'portfolio', 'analysis', 'alerts', 'watchlist', 'dashboard', 'auth'] 