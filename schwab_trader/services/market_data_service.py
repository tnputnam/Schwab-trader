"""Market data service with fallback options."""
import os
from typing import Dict, Optional
import yfinance as yf
import requests
from datetime import datetime, timedelta
from flask import current_app, session
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)

class MarketDataService:
    """Service for handling market data with fallback options."""
    
    def __init__(self):
        """Initialize the market data service."""
        self.alpha_vantage_key = current_app.config.get('ALPHA_VANTAGE_API_KEY')
        self.is_bypassed = session.get('schwab_bypassed', False)
    
    def get_stock_data(self, symbol: str) -> Dict:
        """Get stock data with fallback options."""
        if not self.is_bypassed:
            try:
                # Try Schwab first if not bypassed
                return self._get_schwab_data(symbol)
            except Exception as e:
                logger.warning(f"Schwab data fetch failed: {str(e)}")
                # Fall back to alternative sources
                return self._get_fallback_data(symbol)
        else:
            return self._get_fallback_data(symbol)
    
    def _get_schwab_data(self, symbol: str) -> Dict:
        """Get data from Schwab API."""
        # This would be your existing Schwab data fetching logic
        raise NotImplementedError("Schwab data fetching not implemented")
    
    def _get_fallback_data(self, symbol: str) -> Dict:
        """Get data from fallback sources (Alpha Vantage and yfinance)."""
        try:
            # Try Alpha Vantage first
            if self.alpha_vantage_key:
                data = self._get_alpha_vantage_data(symbol)
                if data:
                    return data
            
            # Fall back to yfinance
            return self._get_yfinance_data(symbol)
        except Exception as e:
            logger.error(f"Error getting fallback data: {str(e)}")
            return {"error": str(e)}
    
    def _get_alpha_vantage_data(self, symbol: str) -> Optional[Dict]:
        """Get data from Alpha Vantage."""
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.warning(f"Alpha Vantage fetch failed: {str(e)}")
            return None
    
    def _get_yfinance_data(self, symbol: str) -> Dict:
        """Get data from yfinance."""
        try:
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                "symbol": symbol,
                "price": info.get("regularMarketPrice"),
                "change": info.get("regularMarketChange"),
                "change_percent": info.get("regularMarketChangePercent"),
                "volume": info.get("regularMarketVolume"),
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"yfinance fetch failed: {str(e)}")
            return {"error": str(e)}
    
    def toggle_bypass(self, bypass: bool) -> None:
        """Toggle the bypass mode."""
        session['schwab_bypassed'] = bypass
        logger.info(f"Schwab bypass mode {'enabled' if bypass else 'disabled'}") 