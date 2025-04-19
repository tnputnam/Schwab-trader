import os
import requests
from typing import Dict, List, Optional, Any
from schwab_trader.services.logging_service import LoggingService
from datetime import datetime

logger = LoggingService()

class AlphaVantageAPI:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        logger.info("Initializing AlphaVantageAPI...")
        if not self.api_key:
            logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        logger.info(f"API key found: {self.api_key[:4]}...{self.api_key[-4:]}")
        self.base_url = "https://www.alphavantage.co/query"
        logger.info("AlphaVantageAPI initialized successfully")

    def _make_request(self, params: Dict) -> Dict:
        """Make a request to the Alpha Vantage API."""
        params['apikey'] = self.api_key
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "Error Message" in data:
                logger.error(f"Alpha Vantage API Error: {data['Error Message']}")
                raise ValueError(data["Error Message"])
                
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Alpha Vantage API: {str(e)}")
            raise

    def get_global_quote(self, symbol: str) -> Dict:
        """Get the latest price and volume information for a symbol."""
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol
        }
        return self._make_request(params)

    def get_intraday_data(self, symbol: str, interval: str = "5min") -> Dict:
        """Get intraday time series data for a symbol."""
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "outputsize": "compact"
        }
        return self._make_request(params)

    def get_daily_data(self, symbol: str, outputsize: str = "full") -> Dict:
        """Get daily time series data for a symbol.
        
        Args:
            symbol: The stock symbol to get data for
            outputsize: Either "compact" (last 100 data points) or "full" (full historical data)
        """
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": outputsize
        }
        logger.info(f"Fetching daily data for {symbol} with outputsize={outputsize}")
        data = self._make_request(params)
        if "Time Series (Daily)" in data:
            logger.info(f"Successfully fetched {len(data['Time Series (Daily)'])} days of data for {symbol}")
        return data

    def search_symbols(self, keywords: str) -> List[Dict]:
        """Search for symbols and companies matching the keywords."""
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords
        }
        data = self._make_request(params)
        return data.get("bestMatches", [])

    def get_company_overview(self, symbol: str) -> Dict:
        """Get company overview information."""
        params = {
            "function": "OVERVIEW",
            "symbol": symbol
        }
        return self._make_request(params)

    def get_market_status(self) -> Dict:
        """Get the current market status."""
        params = {
            "function": "MARKET_STATUS"
        }
        return self._make_request(params)

    def get_top_gainers_losers(self) -> Dict:
        """Get the top gainers and losers in the market."""
        params = {
            "function": "TOP_GAINERS_LOSERS"
        }
        return self._make_request(params)

    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """
        Get historical price data for a symbol from Alpha Vantage
        
        Args:
            symbol: Stock symbol
            start_date: Start date for historical data
            end_date: End date for historical data
            
        Returns:
            List of dictionaries containing historical price data
        """
        try:
            # Get daily adjusted data
            function = 'TIME_SERIES_DAILY_ADJUSTED'
            url = f'{self.base_url}/query?function={function}&symbol={symbol}&outputsize=full&apikey={self.api_key}'
            
            response = requests.get(url)
            if response.status_code != 200:
                logger.error(f"Error getting data from Alpha Vantage: {response.status_code}")
                return []
            
            data = response.json()
            if 'Time Series (Daily)' not in data:
                logger.error(f"No data returned from Alpha Vantage for {symbol}")
                return []
            
            # Convert data to list of dictionaries
            daily_data = data['Time Series (Daily)']
            result = []
            
            for date_str, values in daily_data.items():
                date = datetime.strptime(date_str, '%Y-%m-%d')
                if start_date <= date <= end_date:
                    result.append({
                        'date': date_str,
                        'open': float(values['1. open']),
                        'high': float(values['2. high']),
                        'low': float(values['3. low']),
                        'close': float(values['4. close']),
                        'volume': int(values['6. volume'])
                    })
            
            # Sort by date
            result.sort(key=lambda x: x['date'])
            
            logger.info(f"Retrieved {len(result)} data points from Alpha Vantage for {symbol}")
            return result
            
        except Exception as e:
            logger.error(f"Error getting historical data from Alpha Vantage for {symbol}: {str(e)}")
            return [] 