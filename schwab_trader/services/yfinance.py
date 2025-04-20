import yfinance as yf
from schwab_trader.services.logging_service import LoggingService
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import time
import json
from requests.exceptions import RequestException
import pandas as pd

class YFinanceAPI:
    def __init__(self, max_retries: int = 3, retry_delay: float = 2.0):
        self.logger = LoggingService()
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Minimum time between requests in seconds
        self._cache = {}  # Initialize cache dictionary
        
        # Configure yfinance to use a proxy if needed
        yf.set_tz_cache_location("yfinance_cache")

    def _get_cache_key(self, symbol: str, start_date: datetime, end_date: datetime) -> str:
        """Generate a unique cache key for the given parameters"""
        return f"{symbol}_{start_date.strftime('%Y-%m-%d')}_{end_date.strftime('%Y-%m-%d')}"

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits by waiting between requests"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last_request)
        self.last_request_time = time.time()

    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get historical price data for a symbol from Yahoo Finance with retries and caching
        
        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of dictionaries containing historical price data
        """
        # Check cache first
        cache_key = self._get_cache_key(symbol, start_date, end_date)
        if cache_key in self._cache:
            self.logger.info(f"Retrieved cached data for {symbol}")
            return self._cache[cache_key]
            
        retries = 0
        while retries < self.max_retries:
            try:
                self._wait_for_rate_limit()
                
                # Download data from Yahoo Finance
                ticker = yf.Ticker(symbol)
                df = ticker.history(
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    interval='1d',
                    auto_adjust=True
                )
                
                if df.empty:
                    self.logger.warning(f"No data returned from Yahoo Finance for {symbol}, attempt {retries + 1}/{self.max_retries}")
                    retries += 1
                    time.sleep(self.retry_delay * (retries + 1))  # Exponential backoff
                    continue
                
                # Validate the data
                required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
                if not all(col in df.columns for col in required_columns):
                    missing_cols = [col for col in required_columns if col not in df.columns]
                    self.logger.error(f"Missing required columns for {symbol}: {missing_cols}")
                    retries += 1
                    time.sleep(self.retry_delay * (retries + 1))
                    continue
                
                # Convert DataFrame to list of dictionaries
                data = []
                for index, row in df.iterrows():
                    try:
                        data_point = {
                            'date': index.strftime('%Y-%m-%d'),
                            'open': float(row['Open']),
                            'high': float(row['High']),
                            'low': float(row['Low']),
                            'close': float(row['Close']),
                            'volume': int(row['Volume'])
                        }
                        # Validate data point values
                        if all(v is not None and v > 0 for k, v in data_point.items() if k != 'date'):
                            data.append(data_point)
                        else:
                            self.logger.warning(f"Skipping invalid data point for {symbol} on {data_point['date']}")
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f"Error processing data point for {symbol}: {str(e)}")
                        continue
                
                if data:
                    self.logger.info(f"Retrieved {len(data)} valid data points from Yahoo Finance for {symbol}")
                    # Cache the results
                    self._cache[cache_key] = data
                    return data
                else:
                    self.logger.warning(f"No valid data points found for {symbol}, attempt {retries + 1}/{self.max_retries}")
                    retries += 1
                    time.sleep(self.retry_delay * (retries + 1))
                    continue
                
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON decode error for {symbol}: {str(e)}")
                retries += 1
                time.sleep(self.retry_delay * (retries + 1))
                
            except RequestException as e:
                self.logger.error(f"Network error for {symbol}: {str(e)}")
                retries += 1
                time.sleep(self.retry_delay * (retries + 1))
                
            except Exception as e:
                self.logger.error(f"Unexpected error getting data for {symbol}: {str(e)}")
                retries += 1
                time.sleep(self.retry_delay * (retries + 1))
        
        self.logger.error(f"Failed to get data for {symbol} after {self.max_retries} attempts")
        return [] 