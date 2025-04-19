import os
import requests
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

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