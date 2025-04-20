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
        self.min_request_interval = 10.0  # increased to 10 seconds between requests
        self.max_retries = 3
        self.retry_delay = 30.0  # increased to 30 seconds between retries

    def _rate_limit(self):
        """Implement rate limiting"""
        now = time.time()
        time_since_last_request = now - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.info(f"Rate limiting: waiting {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self.last_request_time = time.time()

    def _make_request_with_retry(self, request_func):
        """Make a request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self._rate_limit()
                return request_func()
            except Exception as e:
                if "429" in str(e) and attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (attempt + 1)  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time} seconds before retry {attempt + 1}")
                    time.sleep(wait_time)
                else:
                    raise

    def get_stock_data(self, symbol, period="1mo", interval="1d"):
        """Get stock data with caching."""
        cache_key = f"data_{symbol}_{period}_{interval}"
        if cache_key in self.cache:
            logger.info(f"Retrieved {symbol} data from cache")
            return self.cache[cache_key]
        
        def request_func():
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            
            if len(data) == 0:
                logger.warning(f"No data received for {symbol}")
                raise Exception("No data received")
            
            self.cache[cache_key] = data
            return data
        
        return self._make_request_with_retry(request_func)

def test_yfinance():
    """Test Yahoo Finance API"""
    logger.info("Testing Yahoo Finance API...")
    api = YFinanceWrapper()
    
    try:
        # Test different data retrieval scenarios with more conservative periods
        test_scenarios = [
            ('AAPL', '1mo', '1d'),   # Monthly data with daily intervals
            ('MSFT', '3mo', '1d'),   # 3 months of daily data
            ('GOOGL', '6mo', '1wk')  # 6 months of weekly data
        ]
        
        success_count = 0
        for symbol, period, interval in test_scenarios:
            logger.info(f"\nTesting {symbol} with period={period}, interval={interval}")
            try:
                data = api.get_stock_data(symbol, period=period, interval=interval)
                if len(data) > 0:
                    logger.info(f"Successfully retrieved {len(data)} rows")
                    
                    # Test cache
                    logger.info("Testing cache...")
                    cached_data = api.get_stock_data(symbol, period=period, interval=interval)
                    logger.info("Successfully retrieved data from cache")
                    
                    success_count += 1
                else:
                    logger.error(f"No data received for {symbol}")
            except Exception as e:
                logger.error(f"Error testing {symbol}: {str(e)}")
                continue
        
        if success_count > 0:
            logger.info(f"Yahoo Finance API test successful ({success_count} out of {len(test_scenarios)} scenarios passed)")
            return True
        else:
            logger.error("Yahoo Finance API test failed - no successful scenarios")
            return False
        
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