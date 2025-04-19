import yfinance as yf
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

class YFinanceAPI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Configure yfinance to use a proxy if needed
        yf.set_tz_cache_location("yfinance_cache")

    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get historical price data for a symbol from Yahoo Finance
        
        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of dictionaries containing historical price data
        """
        try:
            # Download data from Yahoo Finance
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval='1d',
                auto_adjust=True
            )
            
            if df.empty:
                self.logger.error(f"No data returned from Yahoo Finance for {symbol}")
                return []
            
            # Convert DataFrame to list of dictionaries
            data = []
            for index, row in df.iterrows():
                data.append({
                    'date': index.strftime('%Y-%m-%d'),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': int(row['Volume'])
                })
            
            self.logger.info(f"Retrieved {len(data)} data points from Yahoo Finance for {symbol}")
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data from Yahoo Finance for {symbol}: {str(e)}")
            return [] 