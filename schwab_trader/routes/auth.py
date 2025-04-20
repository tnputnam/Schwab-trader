"""Authentication routes for the Schwab Trader application."""
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app, render_template, flash
from flask_login import login_user, logout_user, current_user, login_required
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
import requests
from urllib.parse import urlencode
import logging

logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def get_auth_service():
    """Get an instance of AuthService."""
    return AuthService()

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Redirect to Schwab OAuth2 authorization page."""
    if current_user.is_authenticated:
        return redirect(url_for('analysis.dashboard'))
    
    # Generate OAuth2 authorization URL
    auth_url = current_app.config['SCHWAB_AUTH_URL']
    params = {
        'client_id': current_app.config['SCHWAB_CLIENT_ID'],
        'redirect_uri': current_app.config['SCHWAB_REDIRECT_URI'],
        'response_type': 'code',
        'scope': ' '.join(current_app.config['SCHWAB_SCOPES']),
        'state': session.get('state', '')  # Add CSRF protection
    }
    auth_url = f"{auth_url}?{urlencode(params)}"
    return redirect(auth_url)

@auth_bp.route('/callback')
@handle_errors
def callback():
    """Handle OAuth2 callback from Schwab."""
    error = request.args.get('error')
    if error:
        logger.error(f"OAuth2 error: {error}")
        return redirect(url_for('root.index'))
    
    code = request.args.get('code')
    if not code:
        logger.error("No authorization code received")
        return redirect(url_for('root.index'))
    
    # Exchange authorization code for access token
    token_url = current_app.config['SCHWAB_TOKEN_URL']
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': current_app.config['SCHWAB_REDIRECT_URI'],
        'client_id': current_app.config['SCHWAB_CLIENT_ID'],
        'client_secret': current_app.config['SCHWAB_CLIENT_SECRET']
    }
    
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()
        
        # Store tokens in session
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token')
        session['token_type'] = token_data['token_type']
        session['expires_in'] = token_data['expires_in']
        
        # Get user info from Schwab API
        user_info = get_schwab_user_info(token_data['access_token'])
        
        # Create or update user in database
        user = User.query.filter_by(schwab_id=user_info['id']).first()
        if not user:
            user = User(
                username=user_info.get('username', ''),
                email=user_info.get('email', ''),
                schwab_id=user_info['id']
            )
            db.session.add(user)
        else:
            user.username = user_info.get('username', user.username)
            user.email = user_info.get('email', user.email)
        
        db.session.commit()
        login_user(user)
        
        return redirect(url_for('root.index'))
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error exchanging code for token: {str(e)}")
        return redirect(url_for('root.index'))

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user and clear session."""
    logout_user()
    session.clear()
    return redirect(url_for('root.index'))

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

def get_schwab_user_info(access_token):
    """Get user information from Schwab API."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{current_app.config['SCHWAB_API_BASE_URL']}/user",
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting user info: {str(e)}")
        return {'id': 'unknown'} 