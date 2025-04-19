"""Flask application factory for Schwab Trader."""
import os
from flask import Flask
from flask_caching import Cache
from schwab_trader.database import init_db, db
from schwab_trader.utils.logging_utils import setup_logger

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
        portfolio, dashboard, analysis, 
        alerts, watchlist, auth
    )
    app.register_blueprint(root.bp)
    app.register_blueprint(news.bp)
    app.register_blueprint(strategies.bp)
    app.register_blueprint(compare.bp)
    app.register_blueprint(portfolio.bp)
    app.register_blueprint(dashboard)
    app.register_blueprint(analysis.bp)
    app.register_blueprint(alerts.bp)
    app.register_blueprint(watchlist.bp)
    app.register_blueprint(auth.bp)
    
    # Register error handlers
    from schwab_trader.utils.error_utils import AppError
    
    @app.errorhandler(AppError)
    def handle_app_error(error):
        if request.is_json:
            return jsonify({
                'status': 'error',
                'code': error.code,
                'message': error.message,
                'details': error.details
            }), error.status_code
        return render_template('error.html', error=error), error.status_code
    
    @app.errorhandler(404)
    def handle_not_found(error):
        if request.is_json:
            return jsonify({
                'status': 'error',
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }), 404
        return render_template('error.html', error=error), 404
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        logger.error(f"Internal server error: {str(error)}", exc_info=True)
        if request.is_json:
            return jsonify({
                'status': 'error',
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred'
            }), 500
        return render_template('error.html', error=error), 500
    
    return app

# Minimal initialization for now
