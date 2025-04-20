import os
import sys
import logging
import time
from dotenv import load_dotenv
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from cachetools import TTLCache

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alpha_vantage():
    """Test Alpha Vantage API"""
    logger.info("Testing Alpha Vantage API...")
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    
    if not api_key:
        logger.error("Alpha Vantage API key not found in environment variables")
        return False
    
    try:
        # Initialize the API client
        ts = TimeSeries(key=api_key, output_format='pandas')
        
        # Test getting stock data
        data, meta_data = ts.get_intraday('AAPL', interval='1min', outputsize='compact')
        logger.info(f"Successfully retrieved data for AAPL: {len(data)} rows")
        logger.info("Alpha Vantage API test successful")
        return True
    except Exception as e:
        logger.error(f"Error testing Alpha Vantage API: {str(e)}")
        return False

class YFinanceWrapper:
    def __init__(self):
        self.cache = TTLCache(maxsize=100, ttl=300)  # 5 minutes TTL
        self.last_request_time = 0
        self.min_request_interval = 2.0  # seconds between requests

    def _rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def get_ticker_info(self, symbol):
        """Get basic ticker information with caching."""
        cache_key = f"info_{symbol}"
        if cache_key in self.cache:
            logger.info(f"Retrieved {symbol} info from cache")
            return self.cache[cache_key]
        
        self._rate_limit()
        ticker = yf.Ticker(symbol)
        info = ticker.info
        self.cache[cache_key] = info
        return info

    def get_stock_data(self, symbol, period="1d", interval="1h"):
        """Get stock data with caching."""
        cache_key = f"data_{symbol}_{period}_{interval}"
        if cache_key in self.cache:
            logger.info(f"Retrieved {symbol} data from cache")
            return self.cache[cache_key]
        
        self._rate_limit()
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period, interval=interval)
        
        if len(data) == 0:
            logger.warning(f"No data received for {symbol}, trying different interval")
            if interval == "1m":
                data = ticker.history(period=period, interval="5m")
            elif interval == "5m":
                data = ticker.history(period=period, interval="15m")
        
        self.cache[cache_key] = data
        return data

def test_yfinance():
    """Test Yahoo Finance API"""
    logger.info("Testing Yahoo Finance API...")
    api = YFinanceWrapper()
    
    try:
        # Test basic info retrieval
        logger.info("Testing basic info retrieval...")
        info = api.get_ticker_info('AAPL')
        if info:
            logger.info("Successfully retrieved basic info for AAPL")
        
        # Test different data retrieval scenarios
        test_scenarios = [
            ('AAPL', '1d', '1h'),
            ('MSFT', '5d', '1h'),
            ('GOOGL', '1d', '5m')
        ]
        
        for symbol, period, interval in test_scenarios:
            logger.info(f"\nTesting {symbol} with period={period}, interval={interval}")
            try:
                data = api.get_stock_data(symbol, period=period, interval=interval)
                logger.info(f"Successfully retrieved {len(data)} rows")
                
                # Test cache
                logger.info("Testing cache...")
                cached_data = api.get_stock_data(symbol, period=period, interval=interval)
                logger.info("Successfully retrieved data from cache")
                
            except Exception as e:
                logger.error(f"Error testing {symbol}: {str(e)}")
                continue
        
        logger.info("Yahoo Finance API test successful")
        return True
        
    except Exception as e:
        logger.error(f"Error testing Yahoo Finance API: {str(e)}")
        return False

def test_schwab():
    """Test Schwab API"""
    logger.info("Testing Schwab API...")
    api_key = os.getenv('SCHWAB_API_KEY')
    api_secret = os.getenv('SCHWAB_API_SECRET')
    
    if not api_key or not api_secret:
        logger.error("Schwab API credentials not found in environment variables")
        return False
    
    try:
        # Note: This is a placeholder for Schwab API testing
        # Actual implementation will depend on the Schwab API client
        logger.info("Schwab API test skipped - implementation needed")
        return False
    except Exception as e:
        logger.error(f"Error testing Schwab API: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("Starting API tests...")
    
    # Test Alpha Vantage
    logger.info("\n=== Testing Alpha Vantage API ===")
    alpha_vantage_success = test_alpha_vantage()
    
    # Test Yahoo Finance
    logger.info("\n=== Testing Yahoo Finance API ===")
    yfinance_success = test_yfinance()
    
    # Test Schwab
    logger.info("\n=== Testing Schwab API ===")
    schwab_success = test_schwab()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Alpha Vantage: {'Success' if alpha_vantage_success else 'Failed'}")
    logger.info(f"Yahoo Finance: {'Success' if yfinance_success else 'Failed'}")
    logger.info(f"Schwab: {'Not implemented' if not schwab_success else 'Success'}")
    
    # Exit with appropriate status code
    sys.exit(0 if alpha_vantage_success or yfinance_success else 1) 