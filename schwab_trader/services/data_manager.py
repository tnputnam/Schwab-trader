"""Data manager for handling multiple data sources with fallbacks."""
import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from flask import current_app
from schwab_trader.services.schwab_api import SchwabAPI
from alpha_vantage.timeseries import TimeSeries
from schwab_trader.utils.api_utils import retry_on_failure, cache_response, handle_api_error

logger = logging.getLogger(__name__)

class DataManager:
    """Manages data retrieval from multiple sources with fallbacks."""
    
    def __init__(self):
        """Initialize data sources."""
        self.schwab_api = None
        self.alpha_vantage = None
        
        try:
            self.schwab_api = SchwabAPI()
        except Exception as e:
            logger.warning(f"Could not initialize Schwab API: {str(e)}")
        
        try:
            if current_app.config.get('ALPHA_VANTAGE_API_KEY'):
                self.alpha_vantage = TimeSeries(
                    key=current_app.config['ALPHA_VANTAGE_API_KEY'],
                    output_format='pandas'
                )
        except Exception as e:
            logger.warning(f"Could not initialize Alpha Vantage: {str(e)}")
        
        self.data_cache = {}
    
    @retry_on_failure(max_retries=3, delay=1, backoff=2)
    @handle_api_error
    def get_historical_data(self, symbol: str, start_date: datetime, end_date: datetime, source: str = 'auto') -> pd.DataFrame:
        """Get historical data from preferred source with fallbacks."""
        data = None
        
        # Try sources in order of preference
        if source == 'auto':
            sources = ['schwab', 'alpha_vantage', 'yfinance']
        else:
            sources = [source]
        
        for source in sources:
            try:
                if source == 'schwab' and self.schwab_api:
                    data = self._get_schwab_data(symbol, start_date, end_date)
                elif source == 'alpha_vantage' and self.alpha_vantage:
                    data = self._get_alpha_vantage_data(symbol, start_date, end_date)
                elif source == 'yfinance':
                    data = self._get_yfinance_data(symbol, start_date, end_date)
                
                if data is not None and not data.empty:
                    logger.info(f"Successfully retrieved data for {symbol} from {source}")
                    break
            except Exception as e:
                logger.warning(f"Failed to get data from {source} for {symbol}: {str(e)}")
                continue
        
        if data is None or data.empty:
            logger.error(f"Could not retrieve data for {symbol} from any source")
            return None
        
        return data
    
    def _get_schwab_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get data from Schwab API."""
        try:
            response = self.schwab_api.get_historical_prices(
                symbol,
                start_date=start_date,
                end_date=end_date
            )
            return pd.DataFrame(response)
        except Exception as e:
            logger.warning(f"Schwab API failed: {str(e)}")
            return None
    
    def _get_alpha_vantage_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get data from Alpha Vantage."""
        try:
            data, _ = self.alpha_vantage.get_daily_adjusted(
                symbol=symbol,
                outputsize='full'
            )
            data = data[start_date:end_date]
            return data
        except Exception as e:
            logger.warning(f"Alpha Vantage API failed: {str(e)}")
            return None
    
    def _get_yfinance_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get data from Yahoo Finance."""
        try:
            data = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False
            )
            return data
        except Exception as e:
            logger.warning(f"Yahoo Finance failed: {str(e)}")
            return None
    
    def analyze_market_periods(self, symbols: list, years: int = 20) -> dict:
        """Analyze market periods for given symbols."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)
        
        results = {}
        for symbol in symbols:
            data = self.get_historical_data(symbol, start_date, end_date)
            if data is not None:
                results[symbol] = {
                    'bullish': self._find_bullish_period(data),
                    'bearish': self._find_bearish_period(data),
                    'volatile': self._find_volatile_period(data)
                }
        
        self._save_analysis_results(results)
        return results
    
    def _find_bullish_period(self, data: pd.DataFrame) -> dict:
        """Find the most bullish 12-month period."""
        returns = data['Close'].pct_change(periods=252)
        max_return = returns.rolling(window=252).sum().max()
        max_period = returns.rolling(window=252).sum().idxmax()
        return {
            'start_date': max_period - timedelta(days=252),
            'end_date': max_period,
            'return': max_return
        }
    
    def _find_bearish_period(self, data: pd.DataFrame) -> dict:
        """Find the most bearish 12-month period."""
        returns = data['Close'].pct_change(periods=252)
        min_return = returns.rolling(window=252).sum().min()
        min_period = returns.rolling(window=252).sum().idxmin()
        return {
            'start_date': min_period - timedelta(days=252),
            'end_date': min_period,
            'return': min_return
        }
    
    def _find_volatile_period(self, data: pd.DataFrame) -> dict:
        """Find the most volatile 12-month period."""
        volatility = data['Close'].pct_change().rolling(window=252).std()
        max_volatility = volatility.max()
        max_period = volatility.idxmax()
        return {
            'start_date': max_period - timedelta(days=252),
            'end_date': max_period,
            'volatility': max_volatility
        }
    
    def _save_analysis_results(self, results: dict):
        """Save analysis results to a log file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"data/validation/market_analysis_{timestamp}.log"
        
        with open(filename, 'w') as f:
            for symbol, periods in results.items():
                f.write(f"\nAnalysis for {symbol}:\n")
                f.write("=" * 50 + "\n")
                
                f.write("Most Bullish Period:\n")
                f.write(f"Start: {periods['bullish']['start_date']}\n")
                f.write(f"End: {periods['bullish']['end_date']}\n")
                f.write(f"Return: {periods['bullish']['return']:.2%}\n\n")
                
                f.write("Most Bearish Period:\n")
                f.write(f"Start: {periods['bearish']['start_date']}\n")
                f.write(f"End: {periods['bearish']['end_date']}\n")
                f.write(f"Return: {periods['bearish']['return']:.2%}\n\n")
                
                f.write("Most Volatile Period:\n")
                f.write(f"Start: {periods['volatile']['start_date']}\n")
                f.write(f"End: {periods['volatile']['end_date']}\n")
                f.write(f"Volatility: {periods['volatile']['volatility']:.2%}\n\n") 