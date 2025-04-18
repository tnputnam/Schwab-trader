from flask import Blueprint, session, redirect, url_for, request, current_app
from datetime import datetime
import requests
import logging

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/login')
def login():
    """Redirect to Schwab OAuth login page"""
    try:
        # Get authorization URL from Schwab
        auth_url = f"https://api.schwabapi.com/v1/oauth/authorize?client_id={current_app.config['SCHWAB_CLIENT_ID']}&redirect_uri={current_app.config['SCHWAB_REDIRECT_URI']}&response_type=code"
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error in login route: {str(e)}")
        return redirect(url_for('root.index'))

@auth.route('/callback')
def callback():
    """Handle OAuth callback from Schwab"""
    try:
        code = request.args.get('code')
        if not code:
            logger.error("No code received in callback")
            return redirect(url_for('root.index'))

        # Exchange code for token
        token_url = "https://api.schwabapi.com/v1/oauth/token"
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': current_app.config['SCHWAB_CLIENT_ID'],
            'client_secret': current_app.config['SCHWAB_CLIENT_SECRET'],
            'redirect_uri': current_app.config['SCHWAB_REDIRECT_URI']
        }
        
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            logger.error(f"Token exchange failed: {token_response.text}")
            return redirect(url_for('root.index'))

        # Store token in session
        session['schwab_token'] = token_response.json()
        session['schwab_token_expires_at'] = datetime.now().timestamp() + token_response.json()['expires_in']
        
        # Redirect to dashboard
        return redirect(url_for('dashboard.index'))
    except Exception as e:
        logger.error(f"Error in callback route: {str(e)}")
        return redirect(url_for('root.index'))

@auth.route('/logout')
def logout():
    """Clear session and redirect to home"""
    session.clear()
    return redirect(url_for('root.index')) 