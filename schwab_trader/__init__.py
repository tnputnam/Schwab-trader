"""Flask application factory for Schwab Trader."""
import os
import logging
from datetime import datetime
from flask import Flask
from flask_caching import Cache
from schwab_trader.database import init_db, db

# Configure logging
logger = logging.getLogger('schwab_trader')
handler = logging.FileHandler('logs/schwab_trader_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize extensions
cache = Cache()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if test_config is None:
        app.config.from_object('schwab_trader.config.Config')
    else:
        app.config.update(test_config)
    
    # Ensure instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    init_db(app)
    cache.init_app(app)
    
    # Register blueprints
    from schwab_trader.routes import (
        root, news, strategies, compare, 
        portfolio, dashboard, analysis, 
        alerts, watchlist, bp
    )
    app.register_blueprint(root.bp)
    app.register_blueprint(news.bp)
    app.register_blueprint(strategies.bp)
    app.register_blueprint(compare.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(analysis.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(watchlist.bp)
    app.register_blueprint(bp)
    
    logger.info('Schwab Trader startup')
    return app

# Minimal initialization for now
