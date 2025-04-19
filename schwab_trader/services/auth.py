import os
import logging
import requests
from datetime import datetime, timedelta
import json
from flask import current_app

logger = logging.getLogger('schwab_auth')
handler = logging.FileHandler('logs/schwab_auth_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class TokenManager:
    """Manages Schwab API tokens."""
    
    def __init__(self):
        """Initialize the token manager."""
        self.token_file = 'schwab_token.json'
        self.token = None
        self.expires_at = None
        self.load_token()
    
    def load_token(self):
        """Load token from file if it exists and is not expired."""
        try:
            if os.path.exists(self.token_file):
                with open(self.token_file, 'r') as f:
                    data = json.load(f)
                    self.token = data.get('token')
                    self.expires_at = datetime.fromisoformat(data.get('expires_at'))
                    
                    # Check if token is expired or will expire in the next 5 minutes
                    if self.expires_at and self.expires_at > datetime.now() + timedelta(minutes=5):
                        logger.info("Using existing valid token")
                        return
                    else:
                        logger.info("Token expired or will expire soon, refreshing...")
                        self.refresh_token()
            else:
                logger.info("No token file found, getting new token")
                self.refresh_token()
        except Exception as e:
            logger.error(f"Error loading token: {str(e)}")
            self.refresh_token()
    
    def refresh_token(self):
        """Get a new token from Schwab API."""
        try:
            # Get credentials from environment variables
            client_id = current_app.config.get('SCHWAB_CLIENT_ID')
            client_secret = current_app.config.get('SCHWAB_CLIENT_SECRET')
            refresh_token = current_app.config.get('SCHWAB_REFRESH_TOKEN')
            
            if not all([client_id, client_secret, refresh_token]):
                logger.error("Missing required environment variables for Schwab API")
                logger.error(f"CLIENT_ID: {'present' if client_id else 'missing'}")
                logger.error(f"CLIENT_SECRET: {'present' if client_secret else 'missing'}")
                logger.error(f"REFRESH_TOKEN: {'present' if refresh_token else 'missing'}")
                raise ValueError("Missing required environment variables for Schwab API. Please run get_schwab_token.py to set up tokens.")
            
            # Make request to Schwab token endpoint
            url = current_app.config.get('SCHWAB_TOKEN_URL')
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token
            }
            
            logger.info("Requesting new token from Schwab API...")
            response = requests.post(url, headers=headers, data=data)
            response.raise_for_status()
            
            # Parse response
            token_data = response.json()
            self.token = token_data['access_token']
            self.expires_at = datetime.now() + timedelta(seconds=token_data['expires_in'])
            
            # Save token to file
            with open(self.token_file, 'w') as f:
                json.dump({
                    'token': self.token,
                    'expires_at': self.expires_at.isoformat()
                }, f)
            
            logger.info("Successfully refreshed token")
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    def get_token(self):
        """Get the current token, refreshing if necessary."""
        if not self.token or not self.expires_at or self.expires_at <= datetime.now() + timedelta(minutes=5):
            self.refresh_token()
        return self.token

# Create a singleton instance
_token_manager = None

def get_schwab_token():
    """Get the current Schwab API token."""
    global _token_manager
    if _token_manager is None:
        try:
            _token_manager = TokenManager()
        except Exception as e:
            logger.error(f"Error initializing token manager: {str(e)}")
            return None
    return _token_manager.get_token() 