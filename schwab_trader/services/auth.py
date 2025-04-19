import os
import logging
import requests
from datetime import datetime, timedelta
import json

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
            client_id = os.getenv('SCHWAB_CLIENT_ID')
            client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
            refresh_token = os.getenv('SCHWAB_REFRESH_TOKEN')
            
            if not all([client_id, client_secret, refresh_token]):
                raise ValueError("Missing required environment variables for Schwab API")
            
            # Make request to Schwab token endpoint
            url = "https://api.schwabapi.com/v1/oauth/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {
                'grant_type': 'refresh_token',
                'client_id': client_id,
                'client_secret': client_secret,
                'refresh_token': refresh_token
            }
            
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
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise
    
    def get_token(self):
        """Get the current token, refreshing if necessary."""
        if not self.token or not self.expires_at or self.expires_at <= datetime.now() + timedelta(minutes=5):
            self.refresh_token()
        return self.token

# Create a singleton instance
_token_manager = TokenManager()

def get_schwab_token():
    """Get the current Schwab API token."""
    return _token_manager.get_token() 