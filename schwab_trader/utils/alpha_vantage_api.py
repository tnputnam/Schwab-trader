"""Alpha Vantage API utility class."""
import os
from alpha_vantage.timeseries import TimeSeries
from schwab_trader.utils.logger import setup_logger

logger = setup_logger(__name__)

class AlphaVantageAPI:
    """Handles Alpha Vantage API interactions."""
    
    def __init__(self):
        self.connected = False
        self.client = None
        self.api_key = None

    def init_app(self, app):
        """Initialize the API with Flask app context."""
        self.app = app
        self.api_key = app.config.get('ALPHA_VANTAGE_API_KEY')
        if not self.api_key:
            logger.warning("No Alpha Vantage API key found in configuration")
        else:
            logger.info("API key found: " + self.api_key[:4] + "..." + self.api_key[-4:])
        logger.info("Initializing AlphaVantageAPI...")

    def connect(self):
        """Connect to Alpha Vantage API."""
        try:
            if not self.api_key:
                raise ValueError("No Alpha Vantage API key configured")
            
            self.client = TimeSeries(key=self.api_key, output_format='pandas')
            self.connected = True
            logger.info("Connected to Alpha Vantage API")
        except Exception as e:
            logger.error(f"Error connecting to Alpha Vantage API: {str(e)}")
            self.connected = False
            raise

    def disconnect(self):
        """Disconnect from Alpha Vantage API."""
        self.connected = False
        self.client = None
        logger.info("Disconnected from Alpha Vantage API")

    def is_connected(self):
        """Check if connected to Alpha Vantage API."""
        return self.connected

    def get_stock_data(self, symbol, interval='1min'):
        """Get stock data from Alpha Vantage."""
        if not self.connected:
            raise Exception("Not connected to Alpha Vantage API")
        
        try:
            if interval == '1min':
                data, _ = self.client.get_intraday(symbol=symbol, interval='1min', outputsize='compact')
            else:
                data, _ = self.client.get_daily(symbol=symbol, outputsize='compact')
            return data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            raise
    
    def get_technical_indicators(self, symbol, interval='1min', time_period=60):
        """Get technical indicators for a stock"""
        try:
            data, meta_data = self.client.get_sma(symbol=symbol, interval=interval, time_period=time_period)
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