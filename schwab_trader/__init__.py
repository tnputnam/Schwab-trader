"""
Schwab Trader package initialization.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    
    # Check Schwab configuration
    missing_config = config_class.check_schwab_config()
    if missing_config:
        app.logger.warning(f"Missing Schwab configuration: {', '.join(missing_config)}")
    
    # Initialize services within application context
    with app.app_context():
        from schwab_trader.services.alpha_vantage import AlphaVantageAPI
        from schwab_trader.services.schwab import SchwabAPI
        from schwab_trader.services.data_manager import DataManager
        from schwab_trader.services.volume_analysis import VolumeAnalysisService
        from schwab_trader.services.strategy_tester import StrategyTester
        
        # Initialize and cache services
        alpha_vantage = AlphaVantageAPI(app.config['ALPHA_VANTAGE_API_KEY'])
        cache.set('alpha_vantage', alpha_vantage)
        
        schwab_api = SchwabAPI(
            client_id=app.config['SCHWAB_CLIENT_ID'],
            client_secret=app.config['SCHWAB_CLIENT_SECRET'],
            redirect_uri=app.config['SCHWAB_REDIRECT_URI'],
            auth_url=app.config['SCHWAB_AUTH_URL'],
            token_url=app.config['SCHWAB_TOKEN_URL'],
            scopes=app.config['SCHWAB_SCOPES'],
            api_base_url=app.config['SCHWAB_API_BASE_URL']
        )
        cache.set('schwab_api', schwab_api)
        
        data_manager = DataManager(db, alpha_vantage)
        cache.set('data_manager', data_manager)
        
        volume_analysis = VolumeAnalysisService(data_manager)
        cache.set('volume_analysis', volume_analysis)
        
        strategy_tester = StrategyTester(data_manager)
        cache.set('strategy_tester', strategy_tester)
    
    # Register blueprints
    from schwab_trader.routes import auth, main, positions, market_analysis
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(positions.bp)
    app.register_blueprint(market_analysis.bp)
    
    return app
