"""
Schwab Trader package initialization.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from schwab_trader.utils.filters import register_filters
import os

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()

def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    
    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    
    # Default configuration
    db_path = os.path.join(app.instance_path, 'schwab_trader.db')
    app.config.from_mapping(
        SECRET_KEY='dev',
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{db_path}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        CACHE_TYPE='simple',
        CACHE_DEFAULT_TIMEOUT=300,
    )
    
    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.update(test_config)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    
    # Register filters
    register_filters(app)
    
    # Register blueprints
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
    
    # Register CLI commands
    from schwab_trader.cli import create_test_user
    app.cli.add_command(create_test_user)
    
    # Import models for migrations
    from schwab_trader.models import User, Portfolio, Position
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize services within application context
    with app.app_context():
        # Create database tables
        db.create_all()
        
        # Initialize services
        from schwab_trader.services.volume_analysis import VolumeAnalysisService
        from schwab_trader.services.strategy_tester import StrategyTester
        from schwab_trader.services.schwab_market import SchwabMarketAPI
        
        try:
            app.volume_analysis = VolumeAnalysisService()
            app.strategy_tester = StrategyTester()
            app.schwab_market = SchwabMarketAPI()
        except Exception as e:
            app.logger.warning(f"Could not initialize some services: {str(e)}")
    
    return app
