from flask import Blueprint, render_template, redirect, url_for, session
import logging
from datetime import datetime

bp = Blueprint('root', __name__)

# Configure logging
logger = logging.getLogger('root_routes')
handler = logging.FileHandler('logs/root_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/')
def index():
    """Main landing page."""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}")
        return render_template('index.html')

@bp.route('/login')
def login():
    """Login page."""
    try:
        if 'schwab_token' in session:
            return redirect(url_for('dashboard.index'))
        return render_template('login.html')
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return render_template('login.html') 