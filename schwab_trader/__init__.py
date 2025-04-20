"""
Schwab Trader package initialization.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_caching import Cache
import os

from schwab_trader.utils.filters import register_filters

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
        # Set basic configuration
        app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///schwab_trader.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Load additional configuration
        app.config.from_object('schwab_trader.config')
    else:
        # Load the test config if passed in
        if test_config == 'testing':
            app.config.update({
                'TESTING': True,
                'WTF_CSRF_ENABLED': False,
                'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
                'SQLALCHEMY_TRACK_MODIFICATIONS': False,
                'SECRET_KEY': 'test-secret-key'
            })
        else:
            app.config.update(test_config)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    cache.init_app(app)
    login_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Register custom filters
    register_filters(app)
    
    # Import and register blueprints
    from schwab_trader.routes.api import api_bp
    from schwab_trader.routes.auth import auth_bp
    from schwab_trader.routes.root import root_bp
    from schwab_trader.routes.portfolio import portfolio_bp
    from schwab_trader.routes.trading import trading_bp
    from schwab_trader.routes.analysis import analysis_bp
    from schwab_trader.routes.news import news_bp
    from schwab_trader.routes.strategies import bp as strategies_bp
    from schwab_trader.routes.watchlist import bp as watchlist_bp
    from schwab_trader.routes.alerts import bp as alerts_bp
    from schwab_trader.routes.compare import bp as compare_bp
    
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(root_bp)
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
    app.register_blueprint(trading_bp, url_prefix='/trading')
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(news_bp)
    app.register_blueprint(strategies_bp)
    app.register_blueprint(watchlist_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(compare_bp)
    
    # Import models for migrations
    from schwab_trader.models import User, Portfolio, Position
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    return app
