"""Authentication routes for the Schwab Trader application."""
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app, render_template, flash
from flask_login import login_user, logout_user, current_user
from schwab_trader.utils.error_utils import (
    handle_errors, AuthenticationError, ValidationError,
    handle_api_error
)
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.services.auth_service import AuthService
from schwab_trader.models.user import User
from schwab_trader.utils.schwab_oauth import SchwabOAuth
from schwab_trader.services.market_data_service import MarketDataService
from schwab_trader.services.schwab_service import get_schwab_oauth
from schwab_trader.utils.auth import get_auth_url, get_token, refresh_token, is_authenticated
from schwab_trader.forms.auth import LoginForm

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = get_logger(__name__)

def get_auth_service():
    """Get an instance of AuthService."""
    return AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('analysis.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return render_template('auth/login.html', form=form), 401
        
        login_user(user, remember=form.remember_me.data)
        session['schwab_token'] = {'access_token': 'demo_token'}  # For demo purposes
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('analysis.dashboard')
        return redirect(next_page)
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/callback')
@handle_errors
def callback():
    """Handle OAuth callback."""
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code provided'}), 400
    
    token = get_token(code)
    session['schwab_token'] = token
    return redirect(url_for('main.index'))

@auth_bp.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('schwab_token', None)
    return redirect(url_for('main.index'))

@auth_bp.route('/refresh')
@handle_errors
def refresh():
    """Refresh the access token."""
    if 'schwab_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    token = refresh_token(session['schwab_token'])
    session['schwab_token'] = token
    return jsonify({'status': 'success'})

@auth_bp.route('/status')
def status():
    """Check authentication status."""
    return jsonify({'authenticated': is_authenticated()})

@auth_bp.route('/api/refresh_token')
@handle_api_error
@handle_errors
def refresh_token_api():
    """Refresh access token."""
    if not current_user.is_authenticated:
        raise AuthenticationError()
    
    try:
        auth_service = get_auth_service()
        tokens = auth_service.refresh_token(current_user.refresh_token)
        if not tokens:
            raise AuthenticationError("Failed to refresh token")
        
        current_user.update_tokens(tokens)
        return jsonify({
            'status': 'success',
            'message': 'Token refreshed successfully'
        })
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise AuthenticationError(details=str(e))

@auth_bp.route('/api/check_auth')
@handle_errors
def check_auth():
    """Check authentication status."""
    return jsonify({
        'status': 'success',
        'authenticated': current_user.is_authenticated,
        'user': {
            'email': current_user.email if current_user.is_authenticated else None,
            'name': current_user.name if current_user.is_authenticated else None
        }
    })

@auth_bp.route('/bypass', methods=['GET', 'POST'])
def toggle_bypass():
    """Toggle the Schwab bypass mode."""
    try:
        if request.method == 'GET':
            # Check current bypass status
            bypassed = session.get('schwab_bypassed', False)
            return jsonify({
                'status': 'success',
                'bypassed': bypassed
            })
        
        # Handle POST request
        bypass = request.json.get('bypass', False)
        market_data_service = MarketDataService()
        market_data_service.toggle_bypass(bypass)
        session['schwab_bypassed'] = bypass
        
        if bypass:
            # If enabling bypass, return success without redirect
            return jsonify({
                'status': 'success',
                'message': 'Schwab bypass enabled',
                'bypassed': True
            })
        
        return jsonify({
            'status': 'success',
            'message': 'Schwab bypass disabled',
            'bypassed': False
        })
    except Exception as e:
        logger.error(f"Error toggling bypass: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@auth_bp.route('/force_bypass_off', methods=['POST'])
def force_bypass_off():
    """Force the Schwab bypass mode to be turned off."""
    try:
        market_data_service = MarketDataService()
        market_data_service.toggle_bypass(False)
        session['schwab_bypassed'] = False
        
        return jsonify({
            'status': 'success',
            'message': 'Schwab bypass disabled',
            'bypassed': False
        })
    except Exception as e:
        logger.error(f"Error forcing bypass off: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@auth_bp.route('/schwab')
def schwab_auth():
    """Initiate Schwab OAuth flow."""
    try:
        client = get_schwab_oauth()
        auth_url = client.prepare_request_uri(
            current_app.config['SCHWAB_AUTH_URL'],
            redirect_uri=current_app.config['SCHWAB_REDIRECT_URI'],
            scope=['trading', 'accounts']
        )
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error initiating Schwab auth: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 