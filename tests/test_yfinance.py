import unittest
from datetime import datetime, timedelta
from schwab_trader.services.yfinance import YFinanceAPI
import time
from unittest.mock import patch, MagicMock
import pandas as pd

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
        
        # Create mock data
        self.mock_data = pd.DataFrame({
            'Open': [150.0, 151.0],
            'High': [155.0, 156.0],
            'Low': [149.0, 150.0],
            'Close': [153.0, 154.0],
            'Volume': [1000000, 1100000]
        }, index=pd.date_range(start=self.start_date, periods=2))

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

    @patch('yfinance.Ticker')
    def test_get_historical_data(self, mock_ticker):
        """Test getting historical data"""
        # Configure mock
        mock_instance = MagicMock()
        mock_instance.history.return_value = self.mock_data
        mock_ticker.return_value = mock_instance
        
        for symbol in self.valid_symbols:
            data = self.api.get_historical_data(
                symbol=symbol,
                start_date=self.start_date,
                end_date=self.end_date
            )
            self.assertTrue(self.validate_price_data(data))
            self.assertGreater(len(data), 0)
            
        # Test invalid symbol
        mock_instance.history.return_value = pd.DataFrame()  # Empty DataFrame for invalid symbol
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

    @patch('yfinance.Ticker')
    def test_caching(self, mock_ticker):
        """Test caching functionality"""
        # Configure mock
        mock_instance = MagicMock()
        mock_instance.history.return_value = self.mock_data
        mock_ticker.return_value = mock_instance
        
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

    @patch('yfinance.Ticker')
    def test_retry_logic(self, mock_ticker):
        """Test retry logic with invalid symbol"""
        # Configure mock to raise an exception
        mock_instance = MagicMock()
        mock_instance.history.side_effect = Exception("API Error")
        mock_ticker.return_value = mock_instance
        
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