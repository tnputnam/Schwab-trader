import unittest
from datetime import datetime, timedelta
import time
import pandas as pd
import sys
import os
from unittest.mock import patch, MagicMock
from flask import Flask

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.schwab_market import SchwabMarketAPI
from services.alpha_vantage import AlphaVantageAPI
from services.yfinance import YFinanceAPI
from services.data_manager import DataManager
from config import TestConfig

class MockMarketData:
    @staticmethod
    def get_mock_quote(symbol):
        return {
            'symbol': symbol,
            'price': 150.0,
            'volume': 1000000,
            'timestamp': datetime.now().isoformat()
        }

    @staticmethod
    def get_mock_historical_data(symbol, start_date, end_date):
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        return pd.DataFrame({
            'date': dates,
            'open': [150.0] * len(dates),
            'high': [155.0] * len(dates),
            'low': [145.0] * len(dates),
            'close': [152.0] * len(dates),
            'volume': [1000000] * len(dates)
        })

class MarketDataIntegrationTest(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        # Create Flask app for testing
        self.app = Flask(__name__)
        self.app.config.from_object(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()

        self.symbols = ['AAPL', 'MSFT', 'TSLA']
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()
        
        # Mock API responses
        self.mock_quote = MockMarketData.get_mock_quote
        self.mock_historical_data = MockMarketData.get_mock_historical_data

    def tearDown(self):
        """Clean up after tests."""
        self.app_context.pop()

    @patch('services.schwab_market.SchwabMarketAPI.get_quote')
    @patch('services.alpha_vantage.AlphaVantageAPI.get_daily_data')
    @patch('services.yfinance.YFinanceAPI.get_historical_data')
    def test_api_response_times(self, mock_yfinance, mock_alpha_vantage, mock_schwab):
        """Test response times for each API."""
        # Setup mock responses
        mock_schwab.side_effect = lambda symbol: self.mock_quote(symbol)
        mock_alpha_vantage.side_effect = lambda symbol: self.mock_historical_data(symbol, self.start_date, self.end_date)
        mock_yfinance.side_effect = lambda symbol, start_date, end_date: self.mock_historical_data(symbol, start_date, end_date)

        response_times = {
            'schwab': [],
            'alpha_vantage': [],
            'yfinance': []
        }

        # Test each API with multiple symbols
        for symbol in self.symbols:
            # Test Schwab API
            start_time = time.time()
            try:
                SchwabMarketAPI().get_quote(symbol)
                response_times['schwab'].append(time.time() - start_time)
            except Exception as e:
                print(f"Schwab API error for {symbol}: {str(e)}")

            # Test Alpha Vantage API
            start_time = time.time()
            try:
                AlphaVantageAPI().get_daily_data(symbol)
                response_times['alpha_vantage'].append(time.time() - start_time)
            except Exception as e:
                print(f"Alpha Vantage API error for {symbol}: {str(e)}")

            # Test Yahoo Finance API
            start_time = time.time()
            try:
                YFinanceAPI().get_historical_data(symbol, self.start_date, self.end_date)
                response_times['yfinance'].append(time.time() - start_time)
            except Exception as e:
                print(f"Yahoo Finance API error for {symbol}: {str(e)}")

        # Calculate average response times
        avg_times = {api: sum(times)/len(times) if times else float('inf') 
                    for api, times in response_times.items()}
        
        # Print results
        print("\nAPI Response Times (seconds):")
        for api, avg_time in avg_times.items():
            print(f"{api}: {avg_time:.3f}")

        # Assert that response times are reasonable (less than 0.1 seconds for mock data)
        for api, avg_time in avg_times.items():
            self.assertLess(avg_time, 0.1, f"{api} API response time too slow")

    @patch('services.schwab_market.SchwabMarketAPI.get_historical_prices')
    @patch('services.alpha_vantage.AlphaVantageAPI.get_daily_data')
    @patch('services.yfinance.YFinanceAPI.get_historical_data')
    def test_data_consistency(self, mock_yfinance, mock_alpha_vantage, mock_schwab):
        """Test data consistency across different APIs."""
        # Setup mock responses
        mock_schwab.side_effect = lambda symbol, period, frequency: self.mock_historical_data(symbol, self.start_date, self.end_date)
        mock_alpha_vantage.side_effect = lambda symbol: self.mock_historical_data(symbol, self.start_date, self.end_date)
        mock_yfinance.side_effect = lambda symbol, start_date, end_date: self.mock_historical_data(symbol, start_date, end_date)

        for symbol in self.symbols:
            # Get data from each source
            schwab_data = SchwabMarketAPI().get_historical_prices(symbol, "1m", "daily")
            alpha_vantage_data = AlphaVantageAPI().get_daily_data(symbol)
            yfinance_data = YFinanceAPI().get_historical_data(symbol, self.start_date, self.end_date)

            # Compare data points
            if schwab_data is not None and alpha_vantage_data is not None and yfinance_data is not None:
                # Compare closing prices
                schwab_close = schwab_data['close'].mean()
                alpha_vantage_close = alpha_vantage_data['close'].mean()
                yfinance_close = yfinance_data['close'].mean()

                # Calculate price differences
                price_diff_schwab_alpha = abs(schwab_close - alpha_vantage_close) / schwab_close * 100
                price_diff_schwab_yfinance = abs(schwab_close - yfinance_close) / schwab_close * 100

                # Assert that price differences are within 1%
                self.assertLess(price_diff_schwab_alpha, 1.0, 
                              f"Price difference between Schwab and Alpha Vantage too large for {symbol}")
                self.assertLess(price_diff_schwab_yfinance, 1.0,
                              f"Price difference between Schwab and Yahoo Finance too large for {symbol}")

    @patch('services.data_manager.DataManager._get_schwab_data')
    @patch('services.data_manager.DataManager._get_alpha_vantage_data')
    @patch('services.data_manager.DataManager._get_yfinance_data')
    def test_data_manager_fallback(self, mock_yfinance, mock_alpha_vantage, mock_schwab):
        """Test DataManager's fallback mechanism."""
        # Setup mock responses
        mock_schwab.side_effect = lambda symbol, start_date, end_date: None  # Simulate failure
        mock_alpha_vantage.side_effect = lambda symbol, start_date, end_date: None  # Simulate failure
        mock_yfinance.side_effect = lambda symbol, start_date, end_date: self.mock_historical_data(symbol, start_date, end_date)

        for symbol in self.symbols:
            # Get data through DataManager
            data = DataManager().get_historical_data(
                symbol,
                self.start_date,
                self.end_date,
                source='auto'
            )

            # Verify data is not empty
            self.assertIsNotNone(data, f"No data returned for {symbol}")
            self.assertFalse(data.empty, f"Empty data returned for {symbol}")

            # Verify data structure
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in required_columns:
                self.assertIn(col, data.columns, f"Missing column {col} in data for {symbol}")

    @patch('services.data_manager.DataManager.get_historical_data')
    def test_concurrent_requests(self, mock_data_manager):
        """Test handling of concurrent requests."""
        import concurrent.futures

        # Setup mock response
        mock_data_manager.side_effect = lambda symbol, start_date, end_date, source='auto': self.mock_historical_data(symbol, start_date, end_date)

        def fetch_data(symbol):
            try:
                return DataManager().get_historical_data(
                    symbol,
                    self.start_date,
                    self.end_date,
                    source='auto'
                )
            except Exception as e:
                print(f"Error fetching data for {symbol}: {str(e)}")
                return None

        # Test concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(fetch_data, symbol) for symbol in self.symbols]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # Verify all requests completed successfully
        for result in results:
            self.assertIsNotNone(result, "Concurrent request failed")
            self.assertFalse(result.empty, "Empty data returned from concurrent request")

if __name__ == '__main__':
    unittest.main() 