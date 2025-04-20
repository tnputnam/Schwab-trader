"""Flask application factory for Schwab Trader."""
import os
from flask import Flask
from flask_caching import Cache
from schwab_trader.database import init_db, db
from schwab_trader.utils.logging_utils import setup_logger
from schwab_trader.utils.error_utils import AppError, handle_error

# Initialize extensions
cache = Cache()

# Configure root logger
logger = setup_logger('schwab_trader')

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
        portfolio, analysis, 
        alerts, watchlist, auth, analysis_dashboard
    )
    app.register_blueprint(root.root_bp)
    app.register_blueprint(news.bp)
    app.register_blueprint(strategies.bp)
    app.register_blueprint(compare.bp)
    app.register_blueprint(portfolio.portfolio_bp)
    app.register_blueprint(analysis.bp, url_prefix='/analysis')
    app.register_blueprint(alerts.bp)
    app.register_blueprint(watchlist.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(analysis_dashboard.analysis_dashboard_bp, url_prefix='/analysis/dashboard')
    
    # Register error handlers
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return error.to_response()
    
    @app.errorhandler(404)
    def handle_not_found(error):
        return AppError(
            message="Resource not found",
            status_code=404,
            code="NOT_FOUND"
        ).to_response()
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        return AppError(
            message="An unexpected error occurred",
            status_code=500,
            code="INTERNAL_ERROR"
        ).to_response()
    
    # Register global error handler
    @app.errorhandler(Exception)
    def handle_all_errors(error):
        return handle_error(error)
    
    return app

# Minimal initialization for now
