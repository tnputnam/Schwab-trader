import time
import yfinance as yf
from functools import wraps
from datetime import datetime, timedelta
import pandas as pd
from cachetools import TTLCache, cached
from schwab_trader.utils.logger import setup_logger

logger = setup_logger(__name__)

def rate_limit(calls_per_minute=30):
    """Rate limiting decorator"""
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

class YFinanceAPI:
    def __init__(self):
        self.connected = False
        self.client = None
        # Cache for storing API responses
        self.cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes TTL

    def init_app(self, app):
        """Initialize the API with Flask app context."""
        self.app = app
        logger.info("YFinanceAPI initialized")

    def connect(self):
        """Connect to Yahoo Finance API."""
        try:
            self.client = yf
            self.connected = True
            logger.info("Connected to Yahoo Finance API")
        except Exception as e:
            logger.error(f"Error connecting to Yahoo Finance API: {str(e)}")
            self.connected = False
            raise

    def disconnect(self):
        """Disconnect from Yahoo Finance API."""
        self.connected = False
        self.client = None
        logger.info("Disconnected from Yahoo Finance API")

    def is_connected(self):
        """Check if connected to Yahoo Finance API."""
        return self.connected

    @rate_limit(calls_per_minute=30)
    def get_ticker_info(self, symbol):
        """Get basic ticker information."""
        if not self.connected:
            raise Exception("Not connected to Yahoo Finance API")
        
        cache_key = f"info_{symbol}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            ticker = self.client.Ticker(symbol)
            info = ticker.info
            self.cache[cache_key] = info
            return info
        except Exception as e:
            logger.error(f"Error getting info for {symbol}: {str(e)}")
            raise

    @rate_limit(calls_per_minute=30)
    def get_stock_data(self, symbol, period="1d", interval="1m"):
        """Get stock data from Yahoo Finance."""
        if not self.connected:
            raise Exception("Not connected to Yahoo Finance API")
        
        cache_key = f"data_{symbol}_{period}_{interval}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            ticker = self.client.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if len(data) == 0:
                logger.warning(f"No data received for {symbol}")
                # Try with a different interval if no data
                if interval == "1m":
                    logger.info("Retrying with 5m interval")
                    data = ticker.history(period=period, interval="5m")
                elif interval == "5m":
                    logger.info("Retrying with 15m interval")
                    data = ticker.history(period=period, interval="15m")
            
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting stock data for {symbol}: {str(e)}")
            raise

    @rate_limit(calls_per_minute=30)
    def get_multiple_tickers(self, symbols, period="1d", interval="1m"):
        """Get data for multiple tickers."""
        if not self.connected:
            raise Exception("Not connected to Yahoo Finance API")
        
        cache_key = f"multi_{'_'.join(symbols)}_{period}_{interval}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            data = {}
            for symbol in symbols:
                try:
                    ticker_data = self.get_stock_data(symbol, period, interval)
                    data[symbol] = ticker_data
                except Exception as e:
                    logger.error(f"Error getting data for {symbol}: {str(e)}")
                    continue
            
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error getting multiple ticker data: {str(e)}")
            raise

    def clear_cache(self):
        """Clear the cache."""
        self.cache.clear()
        logger.info("Cache cleared") 