"""Schwab OAuth utility class."""
import os
import logging
from requests_oauthlib import OAuth2Session
from flask import current_app, session, redirect, url_for
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class SchwabOAuth:
    """Handles Schwab OAuth authentication."""
    
    def __init__(self):
        """Initialize the OAuth client."""
        self.client_id = current_app.config['SCHWAB_CLIENT_ID']
        self.client_secret = current_app.config['SCHWAB_CLIENT_SECRET']
        self.redirect_uri = current_app.config['SCHWAB_REDIRECT_URI']
        self.auth_url = current_app.config['SCHWAB_AUTH_URL']
        self.token_url = current_app.config['SCHWAB_TOKEN_URL']
        self.scopes = current_app.config['SCHWAB_SCOPES']
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Schwab API credentials not configured")
    
    def get_authorization_url(self):
        """Get the authorization URL for OAuth flow."""
        oauth = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            scope=self.scopes
        )
        
        authorization_url, state = oauth.authorization_url(
            self.auth_url,
            access_type="offline",
            include_granted_scopes="true"
        )
        
        # Store the state in the session
        session['oauth_state'] = state
        
        return authorization_url
    
    def fetch_token(self, authorization_response):
        """Fetch the access token using the authorization response."""
        oauth = OAuth2Session(
            self.client_id,
            redirect_uri=self.redirect_uri,
            state=session.get('oauth_state')
        )
        
        try:
            token = oauth.fetch_token(
                self.token_url,
                authorization_response=authorization_response,
                client_secret=self.client_secret,
                include_client_id=True
            )
            
            # Store the token in the session
            session['oauth_token'] = token
            
            return token
        except Exception as e:
            logger.error(f"Error fetching token: {str(e)}")
            raise
    
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
            return None
            
        try:
            response = oauth.get(f"{current_app.config['SCHWAB_API_BASE_URL']}/accounts")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return None
    
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