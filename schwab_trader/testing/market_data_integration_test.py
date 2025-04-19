import unittest
from datetime import datetime, timedelta
import time
import pandas as pd
import sys
import os

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.schwab_market import SchwabMarketAPI
from services.alpha_vantage import AlphaVantageAPI
from services.yfinance import YFinanceAPI
from services.data_manager import DataManager

class MarketDataIntegrationTest(unittest.TestCase):
    def setUp(self):
        """Set up test environment."""
        self.symbols = ['AAPL', 'MSFT', 'TSLA']  # Test symbols
        self.start_date = datetime.now() - timedelta(days=30)
        self.end_date = datetime.now()
        self.schwab_api = SchwabMarketAPI()
        self.alpha_vantage = AlphaVantageAPI()
        self.yfinance = YFinanceAPI()
        self.data_manager = DataManager()

    def test_api_response_times(self):
        """Test response times for each API."""
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
                self.schwab_api.get_quote(symbol)
                response_times['schwab'].append(time.time() - start_time)
            except Exception as e:
                print(f"Schwab API error for {symbol}: {str(e)}")

            # Test Alpha Vantage API
            start_time = time.time()
            try:
                self.alpha_vantage.get_daily_data(symbol)
                response_times['alpha_vantage'].append(time.time() - start_time)
            except Exception as e:
                print(f"Alpha Vantage API error for {symbol}: {str(e)}")

            # Test Yahoo Finance API
            start_time = time.time()
            try:
                self.yfinance.get_historical_data(symbol, self.start_date, self.end_date)
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

        # Assert that response times are reasonable (less than 2 seconds)
        for api, avg_time in avg_times.items():
            self.assertLess(avg_time, 2.0, f"{api} API response time too slow")

    def test_data_consistency(self):
        """Test data consistency across different APIs."""
        for symbol in self.symbols:
            # Get data from each source
            schwab_data = None
            alpha_vantage_data = None
            yfinance_data = None

            try:
                schwab_data = self.schwab_api.get_historical_prices(symbol, "1m", "daily")
            except Exception as e:
                print(f"Schwab API error for {symbol}: {str(e)}")

            try:
                alpha_vantage_data = self.alpha_vantage.get_daily_data(symbol)
            except Exception as e:
                print(f"Alpha Vantage API error for {symbol}: {str(e)}")

            try:
                yfinance_data = self.yfinance.get_historical_data(symbol, self.start_date, self.end_date)
            except Exception as e:
                print(f"Yahoo Finance API error for {symbol}: {str(e)}")

            # Compare data points
            if schwab_data and alpha_vantage_data and yfinance_data:
                # Convert to pandas DataFrames for comparison
                schwab_df = pd.DataFrame(schwab_data)
                alpha_vantage_df = pd.DataFrame(alpha_vantage_data)
                yfinance_df = pd.DataFrame(yfinance_data)

                # Compare closing prices
                schwab_close = schwab_df['close'].mean()
                alpha_vantage_close = alpha_vantage_df['close'].mean()
                yfinance_close = yfinance_df['close'].mean()

                # Calculate price differences
                price_diff_schwab_alpha = abs(schwab_close - alpha_vantage_close) / schwab_close * 100
                price_diff_schwab_yfinance = abs(schwab_close - yfinance_close) / schwab_close * 100

                # Assert that price differences are within 1%
                self.assertLess(price_diff_schwab_alpha, 1.0, 
                              f"Price difference between Schwab and Alpha Vantage too large for {symbol}")
                self.assertLess(price_diff_schwab_yfinance, 1.0,
                              f"Price difference between Schwab and Yahoo Finance too large for {symbol}")

    def test_data_manager_fallback(self):
        """Test DataManager's fallback mechanism."""
        for symbol in self.symbols:
            # Get data through DataManager
            data = self.data_manager.get_historical_data(
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

    def test_concurrent_requests(self):
        """Test handling of concurrent requests."""
        import concurrent.futures

        def fetch_data(symbol):
            try:
                return self.data_manager.get_historical_data(
                    symbol,
                    self.start_date,
                    self.end_date
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