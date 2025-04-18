"""Schwab API service for handling API interactions."""
import logging
import requests
from datetime import datetime
from flask import current_app, session

logger = logging.getLogger(__name__)

class SchwabAPI:
    """Handles interactions with the Schwab API."""
    
    def __init__(self):
        """Initialize the Schwab API client."""
        self.base_url = current_app.config['SCHWAB_API_BASE_URL']
        self.token = session.get('schwab_token')
        
        if not self.token:
            raise ValueError("No Schwab token found in session")
    
    def _get_headers(self):
        """Get the headers for API requests."""
        return {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
    
    def get_accounts(self):
        """Get all accounts associated with the token."""
        try:
            response = requests.get(
                f"{self.base_url}/accounts",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise
    
    def get_positions(self, account_id):
        """Get positions for a specific account."""
        try:
            response = requests.get(
                f"{self.base_url}/accounts/{account_id}/positions",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
    
    def get_quotes(self, symbols):
        """Get quotes for multiple symbols."""
        try:
            response = requests.get(
                f"{self.base_url}/marketdata/quotes",
                headers=self._get_headers(),
                params={'symbols': ','.join(symbols)}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting quotes: {str(e)}")
            raise 