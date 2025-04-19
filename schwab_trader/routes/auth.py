"""Authentication routes for Schwab Trader."""
from flask import Blueprint, redirect, url_for, session, request, jsonify, current_app
from flask_login import login_user, logout_user, current_user
from schwab_trader.utils.error_utils import (
    handle_errors, AuthenticationError, ValidationError,
    handle_api_error
)
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.services.auth_service import AuthService
from schwab_trader.models.user import User
from schwab_trader.utils.schwab_oauth import SchwabOAuth

bp = Blueprint('auth', __name__, url_prefix='/auth')
logger = get_logger(__name__)

def get_auth_service():
    """Get an instance of AuthService."""
    return AuthService()

@bp.route('/login', methods=['POST'])
def login():
    """Handle user login."""
    try:
        auth_service = get_auth_service()
        data = request.get_json()
        result = auth_service.login(data)
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@bp.route('/logout', methods=['POST'])
def logout():
    """Handle user logout."""
    try:
        auth_service = get_auth_service()
        result = auth_service.logout()
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@bp.route('/callback')
def oauth_callback():
    """Handle OAuth callback."""
    try:
        auth_service = get_auth_service()
        result = auth_service.handle_oauth_callback(request)
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        return handle_error(e)

@bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh OAuth token."""
    try:
        auth_service = get_auth_service()
        refresh_token = session.get('refresh_token')
        if not refresh_token:
            raise AuthenticationError("No refresh token found")
        result = auth_service.refresh_token(refresh_token)
        if result:
            session['access_token'] = result['access_token']
            session['refresh_token'] = result['refresh_token']
            session['expires_at'] = result['expires_at'].isoformat()
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@bp.route('/status')
def check_auth_status():
    """Check authentication status."""
    try:
        auth_service = get_auth_service()
        result = auth_service.check_auth_status()
        return jsonify(result)
    except Exception as e:
        return handle_error(e)

@bp.route('/api/refresh_token')
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

@bp.route('/api/check_auth')
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