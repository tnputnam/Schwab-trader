from flask import Blueprint, redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from schwab_trader.models import User
from schwab_trader import db
from schwab_trader.utils.schwab_oauth import SchwabOAuth
import logging
import requests
from datetime import datetime, timedelta
import os
import json

auth = Blueprint('auth', __name__)

# Configure logging
logger = logging.getLogger('auth')
handler = logging.FileHandler('logs/auth_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AuthError(Exception):
    """Base class for authentication errors."""
    pass

class TokenError(AuthError):
    """Raised when there's an error with token management."""
    pass

class ConfigError(AuthError):
    """Raised when there's a configuration error."""
    pass

def validate_auth_config():
    """Validate the authentication configuration."""
    required_config = [
        'SCHWAB_CLIENT_ID',
        'SCHWAB_CLIENT_SECRET',
        'SCHWAB_REDIRECT_URI',
        'SCHWAB_AUTH_URL',
        'SCHWAB_TOKEN_URL'
    ]
    
    missing = [key for key in required_config if not current_app.config.get(key)]
    if missing:
        raise ConfigError(f"Missing required configuration: {', '.join(missing)}")

@auth.route('/login')
def login():
    """Redirect to Schwab OAuth login page"""
    try:
        validate_auth_config()
        
        # Store the original URL in the session
        session['next'] = request.args.get('next', url_for('main.index'))
        
        # Initialize OAuth client
        oauth = SchwabOAuth()
        auth_url = oauth.get_authorization_url()
        
        logger.info(f"Redirecting to Schwab OAuth: {auth_url}")
        return redirect(auth_url)
    except ConfigError as e:
        logger.error(f"Configuration error: {str(e)}")
        flash('Authentication configuration error', 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        flash('An error occurred during login', 'error')
        return redirect(url_for('main.index'))

@auth.route('/callback')
def callback():
    """Handle OAuth callback from Schwab"""
    try:
        validate_auth_config()
        
        # Initialize OAuth client
        oauth = SchwabOAuth()
        
        # Exchange code for tokens
        token = oauth.fetch_token(request.url)
        if not token:
            raise TokenError("Failed to exchange code for token")
        
        # Get user info from Schwab
        user_info = get_user_info(token['access_token'])
        if not user_info:
            raise TokenError("Failed to get user information")
        
        # Create or update user
        user = User.query.filter_by(schwab_id=user_info['id']).first()
        if not user:
            user = User(
                schwab_id=user_info['id'],
                email=user_info.get('email'),
                name=user_info.get('name')
            )
            db.session.add(user)
        
        # Update user tokens
        user.access_token = token['access_token']
        user.refresh_token = token['refresh_token']
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token['expires_in'])
        db.session.commit()
        
        # Log in the user
        login_user(user)
        logger.info(f"User {user.id} logged in successfully")
        
        # Store token in session
        session['oauth_token'] = token
        
        # Redirect to the original URL or dashboard
        next_url = session.pop('next', None) or url_for('main.dashboard')
        return redirect(next_url)
        
    except (ConfigError, TokenError) as e:
        logger.error(f"Authentication error: {str(e)}")
        flash(str(e), 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        logger.error(f"Error in callback route: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    try:
        # Clear session data
        session.pop('oauth_token', None)
        session.pop('oauth_state', None)
        session.clear()
        
        # Logout user
        logout_user()
        
        logger.info("User logged out successfully")
        flash('You have been logged out', 'success')
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        flash('An error occurred during logout', 'error')
    return redirect(url_for('main.index'))

def get_user_info(access_token):
    """Get user information from Schwab API"""
    try:
        response = requests.get(
            f"{current_app.config['SCHWAB_API_BASE_URL']}/user",
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            return None
            
        return response.json()
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        return None 