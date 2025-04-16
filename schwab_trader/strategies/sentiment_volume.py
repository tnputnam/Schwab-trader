from .base import TradingStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class SentimentVolumeStrategy(TradingStrategy):
    """Trading strategy based on volume patterns with 30-day baseline"""
    
    def __init__(self, 
                 volume_increase_threshold=1.15,  # 15% increase from baseline
                 min_volume=100000,  # Minimum daily volume requirement
                 lookback_days=30):  # Number of days to calculate volume baseline
        super().__init__(
            name="Volume Baseline Strategy",
            description="Trades based on volume patterns relative to 30-day baseline"
        )
        self.volume_increase_threshold = volume_increase_threshold
        self.min_volume = min_volume
        self.lookback_days = lookback_days
        self.volume_baselines = {}  # Store volume baselines for each symbol
    
    def calculate_volume_baseline(self, volume_data):
        """Calculate 30-day volume baseline"""
        if len(volume_data) < self.lookback_days:
            return None
        
        # Calculate baseline as the average of the last 30 days
        baseline = np.mean(volume_data[-self.lookback_days:])
        return baseline
    
    def analyze_volume_pattern(self, symbol, volume_data):
        """Analyze volume patterns relative to baseline"""
        if len(volume_data) < self.lookback_days:
            return False, False
        
        current_volume = volume_data[-1]
        
        # Calculate or update baseline
        if symbol not in self.volume_baselines:
            self.volume_baselines[symbol] = self.calculate_volume_baseline(volume_data)
        
        baseline = self.volume_baselines[symbol]
        
        # Check if volume meets minimum requirement
        if current_volume < self.min_volume:
            return False, False
        
        # Calculate volume ratio relative to baseline
        volume_ratio = current_volume / baseline
        
        # Buy when volume increases by 15% above baseline
        # Sell when volume returns to baseline
        return (volume_ratio >= self.volume_increase_threshold,
                volume_ratio <= 1.0)  # Return to baseline
    
    def generate_signals(self, data):
        """Generate trading signals based on volume patterns"""
        signals = []
        
        for position in data['positions']:
            symbol = position['symbol']
            
            # Get volume data
            volume_data = position.get('volume_history', [])
            volume_increase, volume_decrease = self.analyze_volume_pattern(symbol, volume_data)
            
            # Generate signals based on volume patterns
            if volume_increase:
                signals.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'reason': f"Volume increased by {((volume_data[-1] / self.volume_baselines[symbol] - 1) * 100):.1f}% above baseline"
                })
            elif volume_decrease:
                signals.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'reason': f"Volume returned to baseline"
                })
            else:
                signals.append({
                    'symbol': symbol,
                    'action': 'HOLD',
                    'reason': f"Volume within normal range"
                })
        
        self.signals.extend(signals)
        return signals
    
    def calculate_position_size(self, portfolio, signal):
        """Calculate position size based on portfolio value and risk parameters"""
        if signal['action'] == 'HOLD':
            return 0
        
        # Use 2% of portfolio value per position
        position_value = portfolio.total_value * 0.02
        
        # Adjust for cash available
        if signal['action'] == 'BUY':
            position_value = min(position_value, portfolio.cash_value)
        
        return position_value
    
    def execute_trades(self, portfolio, signals):
        """Execute trades based on generated signals"""
        executed_trades = []
        
        for signal in signals:
            position_size = self.calculate_position_size(portfolio, signal)
            
            if position_size > 0:
                trade = {
                    'symbol': signal['symbol'],
                    'action': signal['action'],
                    'size': position_size,
                    'reason': signal['reason'],
                    'timestamp': datetime.now()
                }
                executed_trades.append(trade)
        
        return executed_trades 