from typing import Dict, List, Any, Tuple
import pandas as pd
import logging
from datetime import datetime

from schwab_trader.config.market_config import (
    VALIDATION_CONFIG,
    MARKET_PERIODS
)

logger = logging.getLogger(__name__)

class DataValidator:
    def __init__(self):
        self.required_price_fields = VALIDATION_CONFIG['required_price_fields']
        self.required_trade_fields = VALIDATION_CONFIG['required_trade_fields']
        self.valid_trade_types = VALIDATION_CONFIG['valid_trade_types']
        self.min_price = VALIDATION_CONFIG['min_price']
        self.max_price = VALIDATION_CONFIG['max_price']
        self.min_volume = VALIDATION_CONFIG['min_volume']
        self.max_volume = VALIDATION_CONFIG['max_volume']
    
    def validate_price_data(self, prices: List[Dict], market_condition: str) -> Tuple[bool, str]:
        """Validate price data structure and content."""
        try:
            expected_days = MARKET_PERIODS[market_condition]['expected_days']
            if len(prices) != expected_days:
                return False, f"Expected {expected_days} days of data, got {len(prices)}"
            
            for price in prices:
                # Check required fields
                for field in self.required_price_fields:
                    if field not in price:
                        return False, f"Missing price field: {field}"
                
                # Validate price relationships
                if not (self.min_price <= price['low'] <= price['high'] <= self.max_price):
                    return False, f"Price out of range: low={price['low']}, high={price['high']}"
                if not (self.min_volume <= price['volume'] <= self.max_volume):
                    return False, f"Volume out of range: {price['volume']}"
                
                # Validate OHLC relationships
                if not (price['low'] <= price['open'] <= price['high']):
                    return False, f"Invalid OHLC: open={price['open']} not between low={price['low']} and high={price['high']}"
                if not (price['low'] <= price['close'] <= price['high']):
                    return False, f"Invalid OHLC: close={price['close']} not between low={price['low']} and high={price['high']}"
            
            return True, "Price data validation successful"
        except Exception as e:
            return False, f"Error validating price data: {str(e)}"
    
    def validate_trade_data(self, trades: List[Dict]) -> Tuple[bool, str]:
        """Validate trade data structure and content."""
        try:
            for trade in trades:
                # Check required fields
                for field in self.required_trade_fields:
                    if field not in trade:
                        return False, f"Missing trade field: {field}"
                
                # Validate trade values
                if not (self.min_price <= trade['price'] <= self.max_price):
                    return False, f"Trade price out of range: {trade['price']}"
                if not (self.min_volume <= trade['volume'] <= self.max_volume):
                    return False, f"Trade volume out of range: {trade['volume']}"
                if trade['type'] not in self.valid_trade_types:
                    return False, f"Invalid trade type: {trade['type']}"
            
            return True, "Trade data validation successful"
        except Exception as e:
            return False, f"Error validating trade data: {str(e)}"
    
    def calculate_statistics(self, data: Dict) -> Dict[str, Any]:
        """Calculate statistics for validated data."""
        try:
            prices = data['prices']
            trades = data['trades']
            
            # Convert to DataFrame for easier calculations
            price_df = pd.DataFrame(prices)
            
            stats = {
                'price_range': {
                    'min': price_df['low'].min(),
                    'max': price_df['high'].max(),
                    'avg': price_df['close'].mean(),
                    'std': price_df['close'].std(),
                    'daily_returns': price_df['close'].pct_change().std()
                },
                'volume_stats': {
                    'total': price_df['volume'].sum(),
                    'avg': price_df['volume'].mean(),
                    'max': price_df['volume'].max(),
                    'std': price_df['volume'].std()
                },
                'trade_stats': {
                    'total': len(trades),
                    'buy_count': sum(1 for t in trades if t['type'] == 'buy'),
                    'sell_count': sum(1 for t in trades if t['type'] == 'sell'),
                    'avg_trade_volume': sum(t['volume'] for t in trades) / len(trades) if trades else 0
                }
            }
            
            return stats
        except Exception as e:
            logger.error(f"Error calculating statistics: {str(e)}")
            return {}
    
    def validate_data(self, data: Dict, symbol: str, market_condition: str) -> Tuple[bool, Dict[str, Any], str]:
        """Comprehensive data validation."""
        try:
            # Check required fields
            required_fields = ['prices', 'trades', 'market_condition', 'symbol', 'period']
            for field in required_fields:
                if field not in data:
                    return False, {}, f"Missing required field: {field}"
            
            # Validate price data
            price_valid, price_msg = self.validate_price_data(data['prices'], market_condition)
            if not price_valid:
                return False, {}, price_msg
            
            # Validate trade data
            trade_valid, trade_msg = self.validate_trade_data(data['trades'])
            if not trade_valid:
                return False, {}, trade_msg
            
            # Calculate statistics
            stats = self.calculate_statistics(data)
            
            # Log validation results
            logger.info(f"Data validation successful for {symbol} ({market_condition})")
            logger.info(f"Price range: ${stats['price_range']['min']:.2f} - ${stats['price_range']['max']:.2f}")
            logger.info(f"Average volume: {stats['volume_stats']['avg']:,.0f}")
            logger.info(f"Total trades: {stats['trade_stats']['total']} (Buy: {stats['trade_stats']['buy_count']}, Sell: {stats['trade_stats']['sell_count']})")
            
            return True, stats, "Data validation successful"
            
        except Exception as e:
            error_msg = f"Error validating data for {symbol} ({market_condition}): {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg 