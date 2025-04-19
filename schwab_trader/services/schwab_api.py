"""Schwab API service for handling API interactions."""
import logging
from datetime import datetime, timedelta
from flask import current_app
from schwab_trader.utils.schwab_oauth import SchwabOAuth

logger = logging.getLogger(__name__)

class SchwabAPI:
    """Handles interactions with the Schwab API."""
    
    def __init__(self):
        """Initialize the Schwab API client."""
        self.oauth = SchwabOAuth()
        self.base_url = current_app.config['SCHWAB_API_BASE_URL']
    
    def _get_session(self):
        """Get the OAuth session."""
        session = self.oauth.get_oauth_session()
        if not session:
            raise ValueError("No valid OAuth session. Please log in first.")
        return session
    
    def get_accounts(self):
        """Get all accounts associated with the token."""
        try:
            session = self._get_session()
            response = session.get(f"{self.base_url}/accounts")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise
    
    def get_positions(self, account_id):
        """Get positions for a specific account."""
        try:
            session = self._get_session()
            response = session.get(f"{self.base_url}/accounts/{account_id}/positions")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            raise
    
    def get_quotes(self, symbols):
        """Get quotes for multiple symbols."""
        try:
            session = self._get_session()
            response = session.get(
                f"{self.base_url}/marketdata/quotes",
                params={'symbols': ','.join(symbols)}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting quotes: {str(e)}")
            raise
    
    def get_historical_prices(self, symbol, period="1y", frequency="daily"):
        """Get historical price data for a symbol."""
        try:
            # Convert period to start date
            end_date = datetime.now()
            if period == "1m":
                start_date = end_date - timedelta(days=30)
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
            elif period == "6m":
                start_date = end_date - timedelta(days=180)
            elif period == "1y":
                start_date = end_date - timedelta(days=365)
            elif period == "2y":
                start_date = end_date - timedelta(days=730)
            elif period == "5y":
                start_date = end_date - timedelta(days=1825)
            else:
                start_date = end_date - timedelta(days=365)  # Default to 1 year
            
            session = self._get_session()
            response = session.get(
                f"{self.base_url}/marketdata/pricehistory",
                params={
                    'symbol': symbol,
                    'startDate': start_date.strftime('%Y-%m-%d'),
                    'endDate': end_date.strftime('%Y-%m-%d'),
                    'frequencyType': frequency,
                    'needExtendedHoursData': 'false'
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting historical prices for {symbol}: {str(e)}")
            raise 