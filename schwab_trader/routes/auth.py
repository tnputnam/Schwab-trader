from flask import Blueprint, redirect, url_for, session, request, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from schwab_trader.models import User
from schwab_trader import db
import logging
import requests
from datetime import datetime, timedelta
import os

auth = Blueprint('auth', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@auth.route('/login')
def login():
    """Redirect to Schwab OAuth login page"""
    try:
        # Get OAuth configuration from environment variables
        client_id = os.getenv('SCHWAB_CLIENT_ID')
        redirect_uri = os.getenv('SCHWAB_REDIRECT_URI')
        
        if not client_id or not redirect_uri:
            logger.error("Missing OAuth configuration")
            flash('Authentication configuration error', 'error')
            return redirect(url_for('main.index'))
            
        # Store the original URL in the session
        session['next'] = request.args.get('next', url_for('main.index'))
        
        # Construct the OAuth URL
        auth_url = (
            f"https://api.schwabapi.com/v1/oauth/authorize"
            f"?client_id={client_id}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=read"
        )
        
        logger.info(f"Redirecting to Schwab OAuth: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        flash('An error occurred during login', 'error')
        return redirect(url_for('main.index'))

@auth.route('/callback')
def callback():
    """Handle OAuth callback from Schwab"""
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No code received in callback")
            flash('Authentication failed: No authorization code received', 'error')
            return redirect(url_for('main.index'))
            
        # Exchange code for tokens
        token_data = exchange_code_for_tokens(code)
        if not token_data:
            return redirect(url_for('main.index'))
            
        # Get user info from Schwab
        user_info = get_user_info(token_data['access_token'])
        if not user_info:
            return redirect(url_for('main.index'))
            
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
        user.access_token = token_data['access_token']
        user.refresh_token = token_data['refresh_token']
        user.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        db.session.commit()
        
        # Log in the user
        login_user(user)
        logger.info(f"User {user.id} logged in successfully")
        
        # Redirect to the original URL or dashboard
        next_url = session.pop('next', None) or url_for('main.dashboard')
        return redirect(next_url)
        
    except Exception as e:
        logger.error(f"Error in callback route: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return redirect(url_for('main.index'))

@auth.route('/logout')
@login_required
def logout():
    """Logout the current user"""
    try:
        logout_user()
        session.clear()
        logger.info("User logged out successfully")
        flash('You have been logged out', 'success')
    except Exception as e:
        logger.error(f"Error in logout route: {str(e)}")
        flash('An error occurred during logout', 'error')
    return redirect(url_for('main.index'))

def exchange_code_for_tokens(code):
    """Exchange authorization code for access and refresh tokens"""
    try:
        client_id = os.getenv('SCHWAB_CLIENT_ID')
        client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
        redirect_uri = os.getenv('SCHWAB_REDIRECT_URI')
        
        if not all([client_id, client_secret, redirect_uri]):
            logger.error("Missing OAuth configuration for token exchange")
            flash('Authentication configuration error', 'error')
            return None
            
        response = requests.post(
            'https://api.schwabapi.com/v1/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirect_uri,
                'client_id': client_id,
                'client_secret': client_secret
            }
        )
        
        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            flash('Authentication failed: Could not exchange authorization code', 'error')
            return None
            
        return response.json()
    except Exception as e:
        logger.error(f"Error exchanging code for tokens: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return None

def get_user_info(access_token):
    """Get user information from Schwab API"""
    try:
        response = requests.get(
            'https://api.schwabapi.com/v1/user',
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            flash('Authentication failed: Could not retrieve user information', 'error')
            return None
            
        return response.json()
    except Exception as e:
        logger.error(f"Error getting user info: {str(e)}")
        flash('An error occurred during authentication', 'error')
        return None 