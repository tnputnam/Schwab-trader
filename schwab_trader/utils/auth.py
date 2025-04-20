"""Authentication utilities for the Schwab Trader application."""
import os
from flask import current_app, session
from schwab_trader.utils.error_handling import handle_errors
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def get_auth_url():
    """Get the Schwab OAuth authorization URL."""
    client_id = current_app.config['SCHWAB_CLIENT_ID']
    redirect_uri = current_app.config['SCHWAB_REDIRECT_URI']
    return f"https://api.schwabapi.com/v1/oauth/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code"

@handle_errors
def get_token(code):
    """Get access token using authorization code."""
    client_id = current_app.config['SCHWAB_CLIENT_ID']
    client_secret = current_app.config['SCHWAB_CLIENT_SECRET']
    redirect_uri = current_app.config['SCHWAB_REDIRECT_URI']
    
    # TODO: Implement actual token request to Schwab API
    # This is a placeholder implementation
    return {
        'access_token': 'dummy_access_token',
        'refresh_token': 'dummy_refresh_token',
        'expires_in': 3600
    }

@handle_errors
def refresh_token(token):
    """Refresh the access token."""
    client_id = current_app.config['SCHWAB_CLIENT_ID']
    client_secret = current_app.config['SCHWAB_CLIENT_SECRET']
    
    # TODO: Implement actual token refresh with Schwab API
    # This is a placeholder implementation
    return {
        'access_token': 'dummy_new_access_token',
        'refresh_token': 'dummy_new_refresh_token',
        'expires_in': 3600
    }

def get_access_token():
    """Get valid access token, refreshing if necessary."""
    if not session.get('access_token'):
        return None
    
    # Check if token is expired
    expires_at = session.get('expires_at')
    if expires_at and datetime.utcnow() > datetime.fromisoformat(expires_at):
        return refresh_access_token()
    
    return session['access_token']

def refresh_access_token():
    """Refresh the access token using refresh token."""
    refresh_token = session.get('refresh_token')
    if not refresh_token:
        logger.error("No refresh token available")
        return None
    
    try:
        response = requests.post(
            current_app.config['SCHWAB_TOKEN_URL'],
            data={
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token,
                'client_id': current_app.config['SCHWAB_CLIENT_ID'],
                'client_secret': current_app.config['SCHWAB_CLIENT_SECRET']
            }
        )
        response.raise_for_status()
        token_data = response.json()
        
        # Update session with new tokens
        session['access_token'] = token_data['access_token']
        session['refresh_token'] = token_data.get('refresh_token', refresh_token)
        session['token_type'] = token_data['token_type']
        session['expires_in'] = token_data['expires_in']
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        session['expires_at'] = expires_at.isoformat()
        
        return token_data['access_token']
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error refreshing token: {str(e)}")
        return None

def make_schwab_request(method, endpoint, **kwargs):
    """Make an authenticated request to the Schwab API."""
    access_token = get_access_token()
    if not access_token:
        raise ValueError("No valid access token available")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    
    if 'headers' in kwargs:
        headers.update(kwargs.pop('headers'))
    
    url = f"{current_app.config['SCHWAB_API_BASE_URL']}{endpoint}"
    
    try:
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error making Schwab API request: {str(e)}")
        raise

def is_authenticated():
    """Check if user is authenticated with valid tokens."""
    return bool(get_access_token()) 