"""Schwab OAuth utility class."""
import os
import logging
import requests
from requests_oauthlib import OAuth2Session
from flask import current_app, session, redirect, url_for
from urllib.parse import urlencode
from datetime import datetime, timedelta
import json

logger = logging.getLogger('schwab_oauth')
handler = logging.FileHandler('logs/schwab_oauth_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class OAuthError(Exception):
    """Base class for OAuth errors."""
    pass

class TokenError(OAuthError):
    """Raised when there's an error with token management."""
    pass

class ConfigError(OAuthError):
    """Raised when there's a configuration error."""
    pass

class SchwabOAuth:
    """Handles Schwab OAuth authentication."""
    
    def __init__(self):
        """Initialize the OAuth client."""
        self._validate_config()
        self.client_id = current_app.config['SCHWAB_CLIENT_ID']
        self.client_secret = current_app.config['SCHWAB_CLIENT_SECRET']
        self.redirect_uri = current_app.config['SCHWAB_REDIRECT_URL']
        self.auth_url = current_app.config['SCHWAB_AUTH_URL']
        self.token_url = current_app.config['SCHWAB_TOKEN_URL']
        self.scopes = current_app.config['SCHWAB_SCOPES']
        
        # Debug log the configuration
        logger.debug("OAuth Configuration:")
        logger.debug(f"Client ID: {self.client_id}")
        logger.debug(f"Auth URL: {self.auth_url}")
        logger.debug(f"Token URL: {self.token_url}")
        logger.debug(f"Redirect URL: {self.redirect_uri}")
        logger.debug(f"Scopes: {self.scopes}")
    
    def _validate_config(self):
        """Validate the OAuth configuration."""
        required_config = [
            'SCHWAB_CLIENT_ID',
            'SCHWAB_CLIENT_SECRET',
            'SCHWAB_REDIRECT_URL',
            'SCHWAB_AUTH_URL',
            'SCHWAB_TOKEN_URL',
            'SCHWAB_SCOPES'
        ]
        
        missing = [key for key in required_config if not current_app.config.get(key)]
        if missing:
            logger.error(f"Missing required configuration: {', '.join(missing)}")
            raise ConfigError(f"Missing required configuration: {', '.join(missing)}")
    
    def get_authorization_url(self):
        """Get the authorization URL for OAuth flow."""
        try:
            logger.debug("Creating OAuth2Session")
            logger.debug(f"Client ID: {self.client_id}")
            logger.debug(f"Redirect URL: {self.redirect_uri}")
            logger.debug(f"Scopes: {self.scopes}")
            
            # Ensure redirect URL includes /auth/callback
            if not self.redirect_uri.endswith('/auth/callback'):
                self.redirect_uri = f"{self.redirect_uri}/auth/callback"
                logger.debug(f"Updated redirect URL: {self.redirect_uri}")
            
            # Split scopes into a list if it's a string
            if isinstance(self.scopes, str):
                self.scopes = self.scopes.split()
                logger.debug(f"Updated scopes: {self.scopes}")
            
            oauth = OAuth2Session(
                self.client_id,
                redirect_uri=self.redirect_uri,
                scope=self.scopes
            )
            
            logger.debug(f"Getting authorization URL from: {self.auth_url}")
            authorization_url, state = oauth.authorization_url(
                self.auth_url,
                access_type="offline",
                include_granted_scopes="true"
            )
            
            logger.debug(f"Generated authorization URL: {authorization_url}")
            logger.debug(f"Generated state: {state}")
            
            # Store the state in the session
            session['oauth_state'] = state
            
            return authorization_url
        except Exception as e:
            logger.error(f"Error getting authorization URL: {str(e)}")
            logger.error(f"Error type: {type(e)}")
            logger.error(f"Error args: {e.args}")
            raise OAuthError("Failed to get authorization URL")
    
    def fetch_token(self, authorization_response):
        """Fetch the access token using the authorization response."""
        try:
            oauth = OAuth2Session(
                self.client_id,
                redirect_uri=self.redirect_uri,
                state=session.get('oauth_state')
            )
            
            token = oauth.fetch_token(
                self.token_url,
                authorization_response=authorization_response,
                client_secret=self.client_secret,
                include_client_id=True
            )
            
            # Validate token
            if not token or 'access_token' not in token:
                raise TokenError("Invalid token received")
            
            # Store the token in the session
            session['oauth_token'] = token
            
            return token
        except Exception as e:
            logger.error(f"Error fetching token: {str(e)}")
            raise TokenError("Failed to fetch token")
    
    def get_oauth_session(self):
        """Get an OAuth session with the current token."""
        if 'oauth_token' not in session:
            return None
            
        token = session['oauth_token']
        
        return OAuth2Session(
            self.client_id,
            token=token,
            auto_refresh_url=self.token_url,
            auto_refresh_kwargs={
                'client_id': self.client_id,
                'client_secret': self.client_secret
            },
            token_updater=self._token_updater
        )
    
    def _token_updater(self, token):
        """Update the token in the session when it's refreshed."""
        session['oauth_token'] = token
    
    def get_accounts(self):
        """Get the user's accounts."""
        oauth = self.get_oauth_session()
        if not oauth:
            raise TokenError("No valid OAuth session")
            
        try:
            response = oauth.get(f"{current_app.config['SCHWAB_API_BASE_URL']}/accounts")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise TokenError("Failed to get accounts")
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise TokenError("Failed to get accounts")
    
    def get_positions(self, account_id):
        """Get positions for a specific account."""
        oauth = self.get_oauth_session()
        if not oauth:
            return None
            
        try:
            response = oauth.get(f"{current_app.config['SCHWAB_API_BASE_URL']}/accounts/{account_id}/positions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return None
    
    def place_order(self, account_id, order_data):
        """Place an order for a specific account."""
        oauth = self.get_oauth_session()
        if not oauth:
            return None
            
        try:
            response = oauth.post(
                f"{current_app.config['SCHWAB_API_BASE_URL']}/accounts/{account_id}/orders",
                json=order_data
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return None 