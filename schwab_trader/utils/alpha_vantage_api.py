"""Alpha Vantage API utility class."""
import os
import logging
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators

logger = logging.getLogger(__name__)

class AlphaVantageAPI:
    """Handles Alpha Vantage API interactions."""
    
    def __init__(self, app=None):
        """Initialize the API with Flask app context"""
        self.api_key = None
        self.ts = None
        self.ti = None
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the API with Flask app context"""
        self.api_key = app.config.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            logger.warning("No Alpha Vantage API key found in configuration")
            return
            
        logger.info("Initializing AlphaVantageAPI...")
        try:
            self.ts = TimeSeries(key=self.api_key, output_format='pandas')
            self.ti = TechIndicators(key=self.api_key, output_format='pandas')
            logger.info("AlphaVantageAPI initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AlphaVantageAPI: {str(e)}")
            raise
    
    def get_stock_data(self, symbol, interval='1min', outputsize='compact'):
        """Get stock time series data"""
        try:
            data, meta_data = self.ts.get_intraday(symbol=symbol, interval=interval, outputsize=outputsize)
            return data, meta_data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            return None, None
    
    def get_technical_indicators(self, symbol, interval='1min', time_period=60):
        """Get technical indicators for a stock"""
        try:
            data, meta_data = self.ti.get_sma(symbol=symbol, interval=interval, time_period=time_period)
            return data, meta_data
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {str(e)}")
            return None, None
    
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