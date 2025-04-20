"""
Schwab Trader package initialization.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_caching import Cache
from schwab_trader.utils.config_utils import get_config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
cache = Cache()
login_manager = LoginManager()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Load configuration
    if test_config is None:
        app.config.from_object(get_config())
    else:
        app.config.update(test_config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    
    # Import and register blueprints
    from schwab_trader.routes.api import api_bp
    from schwab_trader.routes.auth import bp as auth_bp
    from schwab_trader.routes.root import root_bp
    from schwab_trader.routes.portfolio import portfolio_bp
    from schwab_trader.routes.trading import trading_bp
    from schwab_trader.routes.analysis import analysis_bp
    from schwab_trader.routes.news import news_bp
    from schwab_trader.routes.strategies import strategies_bp
    from schwab_trader.routes.watchlist import watchlist_bp
    from schwab_trader.routes.alerts import alerts_bp
    from schwab_trader.routes.compare import compare_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(root_bp)
    app.register_blueprint(portfolio_bp)
    app.register_blueprint(trading_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(news_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(compare_bp)
    
    # Import models for migrations
    from schwab_trader.models import User, Portfolio, Position, Alert
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
