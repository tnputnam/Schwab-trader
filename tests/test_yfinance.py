import unittest
from datetime import datetime, timedelta
from schwab_trader.services.yfinance import YFinanceAPI
import time

class TestYFinanceAPI(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.api = YFinanceAPI(max_retries=2, retry_delay=1.0)  # Shorter retry settings for tests
        
        # Test symbols
        self.valid_symbols = ['AAPL', 'MSFT', 'GOOGL']
        self.invalid_symbol = 'INVALID_SYMBOL'
        
        # Test date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

    def validate_price_data(self, data):
        """Validate that price data meets our requirements"""
        if not data:
            return False
            
        required_keys = {'date', 'open', 'high', 'low', 'close', 'volume'}
        
        for entry in data:
            # Check all required keys exist
            if not all(key in entry for key in required_keys):
                return False
                
            # Check numeric values are positive
            numeric_keys = {'open', 'high', 'low', 'close', 'volume'}
            if not all(isinstance(entry[key], (int, float)) and entry[key] > 0 
                      for key in numeric_keys):
                return False
                
            # Check date format
            try:
                datetime.strptime(entry['date'], '%Y-%m-%d')
            except ValueError:
                return False
                
        return True

    def test_get_historical_data(self):
        """Test getting historical data"""
        for symbol in self.valid_symbols:
            data = self.api.get_historical_data(
                symbol=symbol,
                start_date=self.start_date,
                end_date=self.end_date
            )
            self.assertTrue(self.validate_price_data(data))
            self.assertGreater(len(data), 0)
            
        # Test invalid symbol
        data = self.api.get_historical_data(
            symbol=self.invalid_symbol,
            start_date=self.start_date,
            end_date=self.end_date
        )
        self.assertEqual(len(data), 0)

    def test_rate_limiting(self):
        """Test rate limiting"""
        start_time = time.time()
        # Make 31 requests (should trigger rate limiting)
        for _ in range(31):
            self.api.get_historical_data(
                symbol='AAPL',
                start_date=self.start_date,
                end_date=self.end_date
            )
        end_time = time.time()
        
        # Should take at least 60 seconds (30 calls per minute)
        self.assertGreater(end_time - start_time, 60)

    def test_caching(self):
        """Test caching functionality"""
        # First request (should hit API)
        start_time = time.time()
        data1 = self.api.get_historical_data(
            symbol='AAPL',
            start_date=self.start_date,
            end_date=self.end_date
        )
        api_time = time.time() - start_time
        
        # Second request (should hit cache)
        start_time = time.time()
        data2 = self.api.get_historical_data(
            symbol='AAPL',
            start_date=self.start_date,
            end_date=self.end_date
        )
        cache_time = time.time() - start_time
        
        # Cache should be faster
        self.assertLess(cache_time, api_time)
        self.assertEqual(data1, data2)

    def test_retry_logic(self):
        """Test retry logic with invalid symbol"""
        start_time = time.time()
        data = self.api.get_historical_data(
            symbol=self.invalid_symbol,
            start_date=self.start_date,
            end_date=self.end_date
        )
        end_time = time.time()
        
        # Should take at least retry_delay * max_retries seconds
        expected_min_time = self.api.retry_delay * self.api.max_retries
        self.assertGreater(end_time - start_time, expected_min_time)
        self.assertEqual(len(data), 0)

if __name__ == '__main__':
    unittest.main() 