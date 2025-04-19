import os
import logging
from datetime import datetime, timedelta
import requests
from schwab_trader.services.auth import get_schwab_token

logger = logging.getLogger('schwab_market')
handler = logging.FileHandler('logs/schwab_market_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class SchwabMarketAPI:
    """Service class for Schwab Market Data API."""
    
    BASE_URL = "https://api.schwabapi.com/marketdata/v1"
    
    def __init__(self):
        """Initialize the Schwab Market API client."""
        self.token = get_schwab_token()
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json'
        }
    
    def get_quote(self, symbol):
        """Get real-time quote for a symbol."""
        try:
            url = f"{self.BASE_URL}/quotes/{symbol}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
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
            
            url = f"{self.BASE_URL}/pricehistory"
            params = {
                'symbol': symbol,
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'frequencyType': frequency,
                'needExtendedHoursData': 'false'
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting historical prices for {symbol}: {str(e)}")
            raise
    
    def get_market_status(self):
        """Get current market status."""
        try:
            url = f"{self.BASE_URL}/markets"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting market status: {str(e)}")
            raise
    
    def get_option_chain(self, symbol, expiration_date=None):
        """Get option chain for a symbol."""
        try:
            url = f"{self.BASE_URL}/chains"
            params = {'symbol': symbol}
            if expiration_date:
                params['expirationDate'] = expiration_date
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting option chain for {symbol}: {str(e)}")
            raise

def get_schwab_market():
    """Get Schwab Market API instance."""
    try:
        return SchwabMarketAPI()
    except Exception as e:
        logger.error(f"Error initializing Schwab Market API: {str(e)}")
        return None 