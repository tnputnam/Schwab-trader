from .base import TradingStrategy
import pandas as pd
import numpy as np

class MomentumStrategy(TradingStrategy):
    """Momentum trading strategy based on price movements and volume"""
    
    def __init__(self, lookback_period=20, volume_threshold=1.5, price_threshold=0.02):
        super().__init__(
            name="Momentum Strategy",
            description="Trades based on price momentum and volume patterns"
        )
        self.lookback_period = lookback_period
        self.volume_threshold = volume_threshold
        self.price_threshold = price_threshold
    
    def generate_signals(self, data):
        """Generate trading signals based on momentum indicators"""
        signals = []
        
        for position in data['positions']:
            # Calculate price momentum
            price_change = position['day_change_percent'] / 100
            volume_ratio = position['volume'] / position.get('avg_volume', position['volume'])
            
            # Generate signals based on momentum and volume
            if price_change > self.price_threshold and volume_ratio > self.volume_threshold:
                signals.append({
                    'symbol': position['symbol'],
                    'action': 'BUY',
                    'reason': f"Strong upward momentum (price: {price_change:.2%}, volume: {volume_ratio:.2f}x)"
                })
            elif price_change < -self.price_threshold and volume_ratio > self.volume_threshold:
                signals.append({
                    'symbol': position['symbol'],
                    'action': 'SELL',
                    'reason': f"Strong downward momentum (price: {price_change:.2%}, volume: {volume_ratio:.2f}x)"
                })
            else:
                signals.append({
                    'symbol': position['symbol'],
                    'action': 'HOLD',
                    'reason': f"Neutral momentum (price: {price_change:.2%}, volume: {volume_ratio:.2f}x)"
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
                    'timestamp': pd.Timestamp.now()
                }
                executed_trades.append(trade)
        
        return executed_trades 