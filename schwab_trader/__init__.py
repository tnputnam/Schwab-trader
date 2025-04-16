from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_migrate import Migrate
import logging
from logging.handlers import RotatingFileHandler
import os
from schwab_trader.models import db
from datetime import datetime

# Initialize extensions
migrate = Migrate()
cache = Cache()

def create_app(test_config=None):
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/schwab_trader.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 5 minutes
    
    # Override with test config if provided
    if test_config:
        app.config.update(test_config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cache.init_app(app)
    
    # Configure login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Configure logging
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app_{}.log'.format(datetime.now().strftime('%Y%m%d')),
                                         maxBytes=10240,
                                         backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Schwab Trader startup')
    
    # Register blueprints
    from schwab_trader.routes import root, news, strategies, compare, portfolio, auth
    app.register_blueprint(root)
    app.register_blueprint(news.bp)
    app.register_blueprint(strategies.bp)
    app.register_blueprint(compare.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(auth)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Start portfolio updater
        from schwab_trader.tasks.portfolio_updater import start_portfolio_updater
        start_portfolio_updater(interval_minutes=5)
    
    @login_manager.user_loader
    def load_user(user_id):
        from schwab_trader.models import User
        return User.query.get(int(user_id))
    
    return app
