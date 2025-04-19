"""Schwab API service for handling API interactions."""
import logging
from datetime import datetime, timedelta
from flask import current_app
from schwab_trader.utils.schwab_oauth import SchwabOAuth
from schwab_trader.utils.api_utils import retry_on_failure, cache_response, handle_api_error

logger = logging.getLogger(__name__)

class SchwabAPI:
    """Handles interactions with the Schwab API."""
    
    def __init__(self):
        """Initialize the Schwab API client."""
        try:
            self.oauth = SchwabOAuth()
            self.base_url = current_app.config['SCHWAB_API_BASE_URL']
        except Exception as e:
            logger.error(f"Error initializing SchwabAPI: {str(e)}")
            raise
    
    def _get_session(self):
        """Get the OAuth session."""
        try:
            session = self.oauth.get_oauth_session()
            if not session:
                logger.error("No valid OAuth session. Please log in first.")
                raise ValueError("No valid OAuth session. Please log in first.")
            return session
        except Exception as e:
            logger.error(f"Error getting OAuth session: {str(e)}")
            raise
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    @handle_api_error
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get_accounts(self):
        """Get all accounts associated with the token."""
        session = self._get_session()
        response = session.get(f"{self.base_url}/accounts")
        response.raise_for_status()
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    @handle_api_error
    @cache_response(timeout=300)  # Cache for 5 minutes
    def get_positions(self, account_id):
        """Get positions for a specific account."""
        session = self._get_session()
        response = session.get(f"{self.base_url}/accounts/{account_id}/positions")
        response.raise_for_status()
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    @handle_api_error
    @cache_response(timeout=60)  # Cache for 1 minute (quotes change frequently)
    def get_quotes(self, symbols):
        """Get quotes for multiple symbols."""
        session = self._get_session()
        response = session.get(
            f"{self.base_url}/marketdata/quotes",
            params={'symbols': ','.join(symbols)}
        )
        response.raise_for_status()
        return response.json()
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    @handle_api_error
    @cache_response(timeout=3600)  # Cache for 1 hour (historical data changes less frequently)
    def get_historical_prices(self, symbol, period="1y", frequency="daily"):
        """Get historical price data for a symbol."""
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