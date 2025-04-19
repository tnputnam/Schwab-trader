from flask import Blueprint, render_template, redirect, url_for, session, jsonify, request
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService

root_bp = Blueprint('root', __name__)
logger = LoggingService()

@root_bp.route('/')
def index():
    """Main landing page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html')

@root_bp.route('/login')
def login():
    """Login page."""
    try:
        if 'schwab_token' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return render_template('login.html') 