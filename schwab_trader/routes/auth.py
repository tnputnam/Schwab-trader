"""Authentication routes for Schwab Trader."""
from flask import Blueprint, redirect, url_for, session, request, jsonify
from flask_login import login_user, logout_user, current_user
from schwab_trader.utils.error_utils import (
    handle_errors, AuthenticationError, ValidationError,
    handle_api_error
)
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.services.auth_service import AuthService
from schwab_trader.models.user import User

bp = Blueprint('auth', __name__)
logger = get_logger(__name__)
auth_service = AuthService()

@bp.route('/login')
@handle_errors
def login():
    """Login page."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return redirect(auth_service.get_auth_url())

@bp.route('/callback')
@handle_errors
def oauth_callback():
    """OAuth callback handler."""
    try:
        code = request.args.get('code')
        if not code:
            raise ValidationError("Authorization code is required")
        
        # Exchange code for tokens
        tokens = auth_service.exchange_code(code)
        if not tokens:
            raise AuthenticationError("Failed to obtain access token")
        
        # Get or create user
        user_info = auth_service.get_user_info(tokens['access_token'])
        user = User.get_or_create(
            email=user_info['email'],
            name=user_info['name']
        )
        
        # Update user tokens
        user.update_tokens(tokens)
        
        # Log in user
        login_user(user)
        
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise AuthenticationError(details=str(e))

@bp.route('/logout')
@handle_errors
def logout():
    """Logout user."""
    logout_user()
    session.clear()
    return redirect(url_for('root.index'))

@bp.route('/api/refresh_token')
@handle_api_error
@handle_errors
def refresh_token():
    """Refresh access token."""
    if not current_user.is_authenticated:
        raise AuthenticationError()
    
    try:
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