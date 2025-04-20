"""Error handling utilities for the Schwab Trader application."""
from functools import wraps
from flask import jsonify, current_app
import logging

def handle_errors(f):
    """Decorator to handle errors in route functions."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error in {f.__name__}: {str(e)}")
            return jsonify({
                'error': str(e),
                'status': 'error'
            }), 500
    return decorated_function

def setup_logging(app):
    """Set up logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    app.logger.setLevel(logging.INFO) 