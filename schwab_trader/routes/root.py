from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request, current_app
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService

root_bp = Blueprint('root', __name__)
logger = LoggingService()

@root_bp.route('/')
def index():
    """Main landing page."""
    try:
        # Check if user is authenticated
        if 'schwab_token' in session:
            logger.info("User is authenticated, redirecting to analysis dashboard")
            return redirect('/analysis/dashboard')
        
        logger.info("Rendering index page for unauthenticated user")
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        current_app.logger.error(f"Template error: {str(e)}", exc_info=True)
        return render_template('error.html', error_message=str(e))

@root_bp.route('/login')
def login():
    """Login page - redirects to auth login."""
    return redirect(url_for('auth.login')) 