from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request, current_app
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService

root_bp = Blueprint('root', __name__)
logger = LoggingService()

@root_bp.route('/')
def index():
    """Main landing page."""
    try:
        logger.info("Attempting to render index page")
        template = render_template('index.html')
        logger.info("Successfully rendered index template")
        return template
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        current_app.logger.error(f"Template error: {str(e)}", exc_info=True)
        return render_template('error.html', error_message=str(e))

@root_bp.route('/login')
def login():
    """Login page."""
    try:
        if 'schwab_token' in session:
            return redirect(url_for('analysis_dashboard.index'))
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return render_template('login.html') 