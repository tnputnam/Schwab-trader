"""Authentication decorators for consistent auth checks."""
from functools import wraps
from flask import session, redirect, url_for, flash
from flask_login import current_user
from schwab_trader.services.logging_service import LoggingService

logger = LoggingService('auth_decorators').logger

def require_schwab_auth(f):
    """Decorator to require Schwab authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if not current_user.is_authenticated or 'oauth_token' not in session:
                logger.warning("Authentication required")
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in auth check: {str(e)}")
            flash('An error occurred during authentication check', 'error')
            return redirect(url_for('main.index'))
    return decorated_function

def require_schwab_token(f):
    """Decorator to require valid Schwab token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            if 'oauth_token' not in session:
                logger.warning("Schwab token required")
                flash('Please log in to access this page', 'warning')
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in token check: {str(e)}")
            flash('An error occurred during token check', 'error')
            return redirect(url_for('main.index'))
    return decorated_function 