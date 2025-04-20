import unittest
from datetime import datetime, timedelta
from schwab_trader.utils.alpha_vantage import AlphaVantageAPI
from schwab_trader import create_app
import os
import time

class TestAlphaVantageAPI(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app({
            'TESTING': True,
            'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY', 'test_key')
        })
        self.api = AlphaVantageAPI()
        self.api.init_app(self.app)
        self.api.connect()
        
        # Test symbols
        self.valid_symbols = ['AAPL', 'MSFT', 'GOOGL']
        self.invalid_symbol = 'INVALID_SYMBOL'
        
        # Test date range
        self.end_date = datetime.now()
        self.start_date = self.end_date - timedelta(days=30)

    def tearDown(self):
        """Clean up after tests"""
        self.api.disconnect()

    def test_connection(self):
        """Test API connection"""
        self.assertTrue(self.api.is_connected())
        
    def test_get_stock_data(self):
        """Test getting stock data"""
        for symbol in self.valid_symbols:
            data = self.api.get_stock_data(symbol)
            self.assertIsNotNone(data)
            self.assertGreater(len(data), 0)
            self.assertIn('Open', data.columns)
            self.assertIn('High', data.columns)
            self.assertIn('Low', data.columns)
            self.assertIn('Close', data.columns)
            self.assertIn('Volume', data.columns)
            
        # Test invalid symbol
        with self.assertRaises(Exception):
            self.api.get_stock_data(self.invalid_symbol)

    def test_get_technical_indicators(self):
        """Test getting technical indicators"""
        for symbol in self.valid_symbols:
            data, meta_data = self.api.get_technical_indicators(symbol)
            self.assertIsNotNone(data)
            self.assertIsNotNone(meta_data)
            self.assertGreater(len(data), 0)
            
        # Test invalid symbol
        data, meta_data = self.api.get_technical_indicators(self.invalid_symbol)
        self.assertIsNone(data)
        self.assertIsNone(meta_data)

    def test_get_quote(self):
        """Test getting real-time quotes"""
        for symbol in self.valid_symbols:
            quote = self.api.get_quote(symbol)
            self.assertIsNotNone(quote)
            self.assertIn('Global Quote', quote)
            
        # Test invalid symbol
        quote = self.api.get_quote(self.invalid_symbol)
        self.assertIsNone(quote)

    def test_get_intraday(self):
        """Test getting intraday data"""
        for symbol in self.valid_symbols:
            data = self.api.get_intraday(symbol)
            self.assertIsNotNone(data)
            self.assertIn('Time Series (5min)', data)
            
        # Test invalid symbol
        data = self.api.get_intraday(self.invalid_symbol)
        self.assertIsNone(data)

    def test_get_daily(self):
        """Test getting daily data"""
        for symbol in self.valid_symbols:
            data = self.api.get_daily(symbol)
            self.assertIsNotNone(data)
            self.assertIn('Time Series (Daily)', data)
            
        # Test invalid symbol
        data = self.api.get_daily(self.invalid_symbol)
        self.assertIsNone(data)

    def test_search_symbols(self):
        """Test symbol search"""
        # Test valid search
        results = self.api.search_symbols('AAPL')
        self.assertIsNotNone(results)
        self.assertIn('bestMatches', results)
        
        # Test invalid search
        results = self.api.search_symbols('')
        self.assertIsNone(results)

    def test_rate_limiting(self):
        """Test rate limiting"""
        start_time = time.time()
        # Make 6 requests (should trigger rate limiting)
        for _ in range(6):
            self.api.get_quote('AAPL')
        end_time = time.time()
        
        # Should take at least 60 seconds (5 calls per minute)
        self.assertGreater(end_time - start_time, 60)

    def test_caching(self):
        """Test caching functionality"""
        # First request (should hit API)
        start_time = time.time()
        data1 = self.api.get_quote('AAPL')
        api_time = time.time() - start_time
        
        # Second request (should hit cache)
        start_time = time.time()
        data2 = self.api.get_quote('AAPL')
        cache_time = time.time() - start_time
        
        # Cache should be faster
        self.assertLess(cache_time, api_time)
        self.assertEqual(data1, data2)

if __name__ == '__main__':
    unittest.main() 