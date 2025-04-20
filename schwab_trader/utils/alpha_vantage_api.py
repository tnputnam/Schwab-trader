"""Alpha Vantage API utility class."""
import os
import logging
import requests
from flask import current_app
from datetime import datetime, timedelta
import json

logger = logging.getLogger('alpha_vantage')
handler = logging.FileHandler('logs/alpha_vantage_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class AlphaVantageAPI:
    """Handles Alpha Vantage API interactions."""
    
    def __init__(self):
        """Initialize the Alpha Vantage API client."""
        logger.info("Initializing AlphaVantageAPI...")
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment variables")
        
        logger.info(f"API key found: {self.api_key[:4]}...{self.api_key[-4:]}")
        self.base_url = "https://www.alphavantage.co/query"
        logger.info("AlphaVantageAPI initialized successfully")
    
    def get_quote(self, symbol):
        """Get real-time quote for a symbol."""
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return None
    
    def get_intraday(self, symbol, interval='5min'):
        """Get intraday data for a symbol."""
        try:
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {str(e)}")
            return None
    
    def get_daily(self, symbol):
        """Get daily data for a symbol."""
        try:
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {str(e)}")
            return None
    
    def search_symbols(self, keywords):
        """Search for symbols matching keywords."""
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error searching symbols for {keywords}: {str(e)}")
            return None 