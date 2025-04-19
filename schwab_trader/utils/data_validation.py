from typing import Dict, List, Any, Tuple, Set
import pandas as pd
import numpy as np
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
        self.volume_spike_threshold = VALIDATION_CONFIG.get('volume_spike_threshold', 3.0)
        self.price_jump_threshold = VALIDATION_CONFIG.get('price_jump_threshold', 0.1)  # 10% daily change
    
    def validate_date_format(self, date_str: str) -> bool:
        """Validate date string format."""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    
    def validate_price_data(self, prices: List[Dict], market_condition: str) -> Tuple[bool, str]:
        """Validate price data structure and content."""
        try:
            expected_days = MARKET_PERIODS[market_condition]['expected_days']
            if len(prices) != expected_days:
                return False, f"Expected {expected_days} days of data, got {len(prices)}"
            
            # Check for duplicate dates
            dates: Set[str] = set()
            for price in prices:
                if not self.validate_date_format(price['date']):
                    return False, f"Invalid date format: {price['date']}"
                if price['date'] in dates:
                    return False, f"Duplicate date found: {price['date']}"
                dates.add(price['date'])
            
            # Convert to DataFrame for advanced validation
            df = pd.DataFrame(prices)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
            
            # Check for gaps in dates
            date_diff = df['date'].diff()
            if not all(date_diff[1:] == pd.Timedelta(days=1)):
                return False, "Gaps found in date sequence"
            
            # Validate price ranges and relationships
            for _, row in df.iterrows():
                if not (self.min_price <= row['low'] <= row['high'] <= self.max_price):
                    return False, f"Price out of range: low={row['low']}, high={row['high']}"
                if not (self.min_volume <= row['volume'] <= self.max_volume):
                    return False, f"Volume out of range: {row['volume']}"
                
                # Validate OHLC relationships
                if not (row['low'] <= row['open'] <= row['high']):
                    return False, f"Invalid OHLC: open={row['open']} not between low={row['low']} and high={row['high']}"
                if not (row['low'] <= row['close'] <= row['high']):
                    return False, f"Invalid OHLC: close={row['close']} not between low={row['low']} and high={row['high']}"
            
            # Check for unusual price movements
            df['price_change'] = df['close'].pct_change()
            if any(abs(df['price_change']) > self.price_jump_threshold):
                return False, f"Unusual price movement detected (> {self.price_jump_threshold*100}% change)"
            
            # Check for volume spikes
            df['volume_ma'] = df['volume'].rolling(window=5, min_periods=1).mean()
            df['volume_ratio'] = df['volume'] / df['volume_ma']
            if any(df['volume_ratio'] > self.volume_spike_threshold):
                return False, f"Unusual volume spike detected (> {self.volume_spike_threshold}x average)"
            
            return True, "Price data validation successful"
        except Exception as e:
            return False, f"Error validating price data: {str(e)}"
    
    def validate_trade_data(self, trades: List[Dict], price_dates: Set[str]) -> Tuple[bool, str]:
        """Validate trade data structure and content."""
        try:
            for trade in trades:
                # Check required fields
                for field in self.required_trade_fields:
                    if field not in trade:
                        return False, f"Missing trade field: {field}"
                
                # Validate date format and range
                if not self.validate_date_format(trade['date']):
                    return False, f"Invalid trade date format: {trade['date']}"
                if trade['date'] not in price_dates:
                    return False, f"Trade date {trade['date']} not in price data range"
                
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
            price_df['date'] = pd.to_datetime(price_df['date'])
            
            # Calculate price statistics
            price_stats = {
                'range': {
                    'min': price_df['low'].min(),
                    'max': price_df['high'].max(),
                    'avg': price_df['close'].mean(),
                    'std': price_df['close'].std()
                },
                'returns': {
                    'daily_std': price_df['close'].pct_change().std(),
                    'max_daily_change': price_df['close'].pct_change().abs().max(),
                    'total_return': (price_df['close'].iloc[-1] / price_df['close'].iloc[0] - 1) * 100
                },
                'volatility': {
                    'daily': price_df['close'].pct_change().std() * np.sqrt(252),  # Annualized
                    'rolling_20d': price_df['close'].pct_change().rolling(window=20).std().mean() * np.sqrt(252)
                }
            }
            
            # Calculate volume statistics
            volume_stats = {
                'total': price_df['volume'].sum(),
                'avg': price_df['volume'].mean(),
                'max': price_df['volume'].max(),
                'std': price_df['volume'].std(),
                'avg_daily_turnover': (price_df['volume'] * price_df['close']).mean()
            }
            
            # Calculate trade statistics
            trade_stats = {
                'total': len(trades),
                'buy_count': sum(1 for t in trades if t['type'] == 'buy'),
                'sell_count': sum(1 for t in trades if t['type'] == 'sell'),
                'avg_trade_volume': sum(t['volume'] for t in trades) / len(trades) if trades else 0,
                'total_trade_volume': sum(t['volume'] for t in trades),
                'avg_trade_price': sum(t['price'] * t['volume'] for t in trades) / sum(t['volume'] for t in trades) if trades else 0
            }
            
            return {
                'price_stats': price_stats,
                'volume_stats': volume_stats,
                'trade_stats': trade_stats
            }
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
            
            # Get price dates for trade validation
            price_dates = {p['date'] for p in data['prices']}
            
            # Validate trade data
            trade_valid, trade_msg = self.validate_trade_data(data['trades'], price_dates)
            if not trade_valid:
                return False, {}, trade_msg
            
            # Calculate statistics
            stats = self.calculate_statistics(data)
            
            # Log validation results
            logger.info(f"Data validation successful for {symbol} ({market_condition})")
            logger.info(f"Price range: ${stats['price_stats']['range']['min']:.2f} - ${stats['price_stats']['range']['max']:.2f}")
            logger.info(f"Total return: {stats['price_stats']['returns']['total_return']:.2f}%")
            logger.info(f"Average daily volume: {stats['volume_stats']['avg']:,.0f}")
            logger.info(f"Total trades: {stats['trade_stats']['total']} (Buy: {stats['trade_stats']['buy_count']}, Sell: {stats['trade_stats']['sell_count']})")
            
            return True, stats, "Data validation successful"
            
        except Exception as e:
            error_msg = f"Error validating data for {symbol} ({market_condition}): {str(e)}"
            logger.error(error_msg)
            return False, {}, error_msg 