"""Authentication service for Schwab Trader."""
from typing import Dict, Optional
import requests
from datetime import datetime, timedelta
from flask import current_app
from schwab_trader.utils.error_utils import ConfigurationError, APIError
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)

class AuthService:
    """Service class for handling authentication."""
    
    def __init__(self):
        """Initialize the auth service."""
        self.validate_config()
    
    def validate_config(self):
        """Validate the authentication configuration."""
        required_config = [
            'SCHWAB_CLIENT_ID',
            'SCHWAB_CLIENT_SECRET',
            'SCHWAB_REDIRECT_URI',
            'SCHWAB_AUTH_URL',
            'SCHWAB_TOKEN_URL',
            'SCHWAB_API_BASE_URL'
        ]
        
        missing = [key for key in required_config if not current_app.config.get(key)]
        if missing:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing)}"
            )
    
    def get_auth_url(self) -> str:
        """Get the authorization URL."""
        params = {
            'client_id': current_app.config['SCHWAB_CLIENT_ID'],
            'redirect_uri': current_app.config['SCHWAB_REDIRECT_URI'],
            'response_type': 'code',
            'scope': 'read write'
        }
        return f"{current_app.config['SCHWAB_AUTH_URL']}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
    
    def exchange_code(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for tokens."""
        try:
            response = requests.post(
                current_app.config['SCHWAB_TOKEN_URL'],
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': current_app.config['SCHWAB_REDIRECT_URI'],
                    'client_id': current_app.config['SCHWAB_CLIENT_ID'],
                    'client_secret': current_app.config['SCHWAB_CLIENT_SECRET']
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                return None
            
            data = response.json()
            return {
                'access_token': data['access_token'],
                'refresh_token': data['refresh_token'],
                'expires_in': data['expires_in'],
                'expires_at': datetime.utcnow() + timedelta(seconds=data['expires_in'])
            }
        except Exception as e:
            logger.error(f"Error exchanging code: {str(e)}")
            raise APIError(details=str(e))
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """Refresh access token using refresh token."""
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
            
            if response.status_code != 200:
                logger.error(f"Token refresh failed: {response.text}")
                return None
            
            data = response.json()
            return {
                'access_token': data['access_token'],
                'refresh_token': data.get('refresh_token', refresh_token),
                'expires_in': data['expires_in'],
                'expires_at': datetime.utcnow() + timedelta(seconds=data['expires_in'])
            }
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise APIError(details=str(e))
    
    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Schwab API."""
        try:
            response = requests.get(
                f"{current_app.config['SCHWAB_API_BASE_URL']}/user",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get user info: {response.text}")
                raise APIError("Failed to get user information")
            
            return response.json()
        except Exception as e:
            logger.error(f"Error getting user info: {str(e)}")
            raise APIError(details=str(e)) 