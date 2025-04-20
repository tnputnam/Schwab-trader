"""Alpha Vantage API utility class."""
import os
import time
from alpha_vantage.timeseries import TimeSeries
from schwab_trader.utils.logger import setup_logger
from cachetools import TTLCache, cached
from functools import wraps
import requests
from datetime import datetime, timedelta

logger = setup_logger(__name__)

def rate_limit(calls_per_minute=5):
    """Rate limiting decorator for Alpha Vantage API"""
    intervals = {}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            func_name = func.__name__
            
            if func_name not in intervals:
                intervals[func_name] = []
            
            # Clean old calls
            intervals[func_name] = [t for t in intervals[func_name] if now - t < 60]
            
            if len(intervals[func_name]) >= calls_per_minute:
                sleep_time = 60 - (now - intervals[func_name][0])
                if sleep_time > 0:
                    logger.info(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                    time.sleep(sleep_time)
            
            result = func(*args, **kwargs)
            intervals[func_name].append(time.time())
            return result
        return wrapper
    return decorator

class AlphaVantageAPI:
    """Handles Alpha Vantage API interactions."""
    
    def __init__(self):
        self.connected = False
        self.client = None
        self.api_key = None
        self.base_url = "https://www.alphavantage.co/query"
        # Initialize cache with 1 hour TTL and max 1000 items
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        self.last_request_time = 0
        self.min_request_interval = 12  # Alpha Vantage free tier allows 5 calls per minute

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

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits by waiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def _get_cache_key(self, function: str, symbol: str, **kwargs) -> str:
        """Generate a unique cache key for the request"""
        params = '_'.join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
        return f"{function}_{symbol}_{params}"

    @rate_limit(calls_per_minute=5)
    def get_stock_data(self, symbol, interval='1min'):
        """Get stock data from Alpha Vantage."""
        if not self.connected:
            raise Exception("Not connected to Alpha Vantage API")
        
        cache_key = self._get_cache_key('stock_data', symbol, interval=interval)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved {symbol} data from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            if interval == '1min':
                data, _ = self.client.get_intraday(symbol=symbol, interval='1min', outputsize='compact')
            else:
                data, _ = self.client.get_daily(symbol=symbol, outputsize='compact')
            
            # Cache the successful result
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            raise
    
    @rate_limit(calls_per_minute=5)
    def get_technical_indicators(self, symbol, interval='1min', time_period=60):
        """Get technical indicators for a stock"""
        cache_key = self._get_cache_key('technical', symbol, interval=interval, time_period=time_period)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved technical indicators for {symbol} from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            data, meta_data = self.client.get_sma(symbol=symbol, interval=interval, time_period=time_period)
            
            # Cache the successful result
            self.cache[cache_key] = (data, meta_data)
            return data, meta_data
        except Exception as e:
            logger.error(f"Error getting technical indicators for {symbol}: {str(e)}")
            return None, None
    
    @rate_limit(calls_per_minute=5)
    def get_quote(self, symbol):
        """Get real-time quote for a symbol."""
        cache_key = self._get_cache_key('quote', symbol)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved quote for {symbol} from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the successful result
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=5)
    def get_intraday(self, symbol, interval='5min'):
        """Get intraday data for a symbol."""
        cache_key = self._get_cache_key('intraday', symbol, interval=interval)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved intraday data for {symbol} from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': symbol,
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the successful result
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting intraday data for {symbol}: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=5)
    def get_daily(self, symbol):
        """Get daily data for a symbol."""
        cache_key = self._get_cache_key('daily', symbol)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved daily data for {symbol} from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            params = {
                'function': 'TIME_SERIES_DAILY',
                'symbol': symbol,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the successful result
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting daily data for {symbol}: {str(e)}")
            return None
    
    @rate_limit(calls_per_minute=5)
    def search_symbols(self, keywords):
        """Search for symbols matching keywords."""
        cache_key = self._get_cache_key('search', keywords)
        cached_data = self.cache.get(cache_key)
        if cached_data is not None:
            logger.info(f"Retrieved symbol search results for {keywords} from cache")
            return cached_data
        
        try:
            self._wait_for_rate_limit()
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords,
                'apikey': self.api_key
            }
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache the successful result
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error searching symbols for {keywords}: {str(e)}")
            return None 