from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from schwab_trader.models import User, db
from schwab_trader.utils.schwab_oauth import SchwabOAuth
import logging
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

__all__ = ['bp']

# Configure logging
logger = logging.getLogger('auth_routes')
handler = logging.FileHandler('logs/auth_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('root.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('root.index'))
        
        flash('Invalid username or password')
    
    return render_template('auth/login.html')

@bp.route('/schwab')
def schwab_auth():
    """Initiate Schwab OAuth flow."""
    try:
        schwab = SchwabOAuth()
        auth_url = schwab.get_auth_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating Schwab auth: {str(e)}")
        return redirect(url_for('root.index'))

@bp.route('/callback')
def callback():
    """Handle OAuth callback from Schwab."""
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No code received in callback")
            return redirect(url_for('root.index'))
            
        schwab = SchwabOAuth()
        token = schwab.get_token(code)
        
        if token:
            session['schwab_token'] = token
            return redirect(url_for('dashboard.index'))
        else:
            logger.error("Failed to get token from Schwab")
            return redirect(url_for('root.index'))
    except Exception as e:
        logger.error(f"Error in Schwab callback: {str(e)}")
        return redirect(url_for('root.index'))

@bp.route('/logout')
def logout():
    """Logout the user and clear session."""
    try:
        session.clear()
        return redirect(url_for('root.index'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        return redirect(url_for('root.index')) 