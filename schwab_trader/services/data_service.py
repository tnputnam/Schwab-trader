import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from schwab_trader.utils.error_utils import APIError, NetworkError, ValidationError
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)

class DataService:
    def __init__(self, api_key: str):
        """Initialize the data service with API key."""
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        
    def _make_request(self, function: str, params: Dict) -> Dict:
        """Make a request to the Alpha Vantage API."""
        try:
            params.update({
                'apikey': self.api_key,
                'function': function
            })
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if "Error Message" in data:
                raise APIError(data["Error Message"])
            if "Note" in data:
                logger.warning(f"API Rate Limit Note: {data['Note']}")
            
            return data
            
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"API request failed: {str(e)}")
        except ValueError as e:
            raise ValidationError(f"Invalid API response: {str(e)}")
    
    def get_stock_quote(self, symbol: str) -> Dict:
        """Get real-time stock quote."""
        params = {
            'symbol': symbol,
            'function': 'GLOBAL_QUOTE'
        }
        data = self._make_request('GLOBAL_QUOTE', params)
        return data.get('Global Quote', {})
    
    def get_intraday_data(self, symbol: str, interval: str = '5min') -> List[Dict]:
        """Get intraday stock data."""
        params = {
            'symbol': symbol,
            'interval': interval,
            'function': 'TIME_SERIES_INTRADAY'
        }
        data = self._make_request('TIME_SERIES_INTRADAY', params)
        time_series = data.get(f'Time Series ({interval})', {})
        
        return [
            {
                'timestamp': datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S'),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            }
            for timestamp, values in time_series.items()
        ]
    
    def get_daily_data(self, symbol: str, output_size: str = 'compact') -> List[Dict]:
        """Get daily stock data."""
        params = {
            'symbol': symbol,
            'outputsize': output_size,
            'function': 'TIME_SERIES_DAILY'
        }
        data = self._make_request('TIME_SERIES_DAILY', params)
        time_series = data.get('Time Series (Daily)', {})
        
        return [
            {
                'date': datetime.strptime(date, '%Y-%m-%d'),
                'open': float(values['1. open']),
                'high': float(values['2. high']),
                'low': float(values['3. low']),
                'close': float(values['4. close']),
                'volume': int(values['5. volume'])
            }
            for date, values in time_series.items()
        ]
    
    def get_company_overview(self, symbol: str) -> Dict:
        """Get company overview information."""
        params = {
            'symbol': symbol,
            'function': 'OVERVIEW'
        }
        data = self._make_request('OVERVIEW', params)
        return data
    
    def search_symbols(self, keywords: str) -> List[Dict]:
        """Search for stock symbols."""
        params = {
            'keywords': keywords,
            'function': 'SYMBOL_SEARCH'
        }
        data = self._make_request('SYMBOL_SEARCH', params)
        return data.get('bestMatches', []) 