from .base import TradingStrategy
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib
from collections import defaultdict

class VolatilityPatternStrategy(TradingStrategy):
    """Strategy to identify and monitor top 15 volatile stocks"""
    
    def __init__(self, 
                 volatility_threshold=0.02,  # 2% daily volatility
                 min_price=5.0,  # Minimum stock price
                 min_volume=100000,  # Minimum daily volume
                 pattern_lookback=20,  # Days to look back for patterns
                 volume_increase_threshold=1.15,  # 15% volume increase
                 volume_decrease_threshold=0.85):  # 15% volume decrease
        super().__init__(
            name="Top Volatile Stocks Strategy",
            description="Monitors top 15 volatile stocks for volume patterns"
        )
        self.volatility_threshold = volatility_threshold
        self.min_price = min_price
        self.min_volume = min_volume
        self.pattern_lookback = pattern_lookback
        self.volume_increase_threshold = volume_increase_threshold
        self.volume_decrease_threshold = volume_decrease_threshold
        self.top_stocks = set()  # Track top 15 volatile stocks
        self.stock_volume_baselines = defaultdict(list)  # Track volume baselines
    
    def calculate_volatility(self, prices):
        """Calculate daily volatility"""
        returns = np.diff(prices) / prices[:-1]
        return np.std(returns)
    
    def select_top_volatile_stocks(self, stock_data):
        """Select top 15 most volatile stocks"""
        volatility_scores = []
        
        for symbol, data in stock_data.items():
            if not data or len(data) < self.pattern_lookback:
                continue
            
            prices = [d['close'] for d in data]
            volumes = [d['volume'] for d in data]
            
            # Check minimum requirements
            if prices[-1] < self.min_price or volumes[-1] < self.min_volume:
                continue
            
            # Calculate volatility
            volatility = self.calculate_volatility(prices)
            
            volatility_scores.append((symbol, volatility))
        
        # Sort by volatility and select top 15
        volatility_scores.sort(key=lambda x: x[1], reverse=True)
        self.top_stocks = {symbol for symbol, _ in volatility_scores[:15]}
        
        # Initialize volume baselines for selected stocks
        for symbol in self.top_stocks:
            volumes = [d['volume'] for d in stock_data[symbol]]
            self.stock_volume_baselines[symbol] = np.mean(volumes[-self.pattern_lookback:])
    
    def analyze_volume_pattern(self, symbol, volumes):
        """Analyze volume patterns for selected stocks"""
        if symbol not in self.top_stocks:
            return False, False
        
        current_volume = volumes[-1]
        baseline = self.stock_volume_baselines[symbol]
        
        # Calculate volume ratios
        volume_ratio = current_volume / baseline
        
        # Buy when volume increases by 15% above baseline
        # Sell when volume decreases by 15% below baseline
        return (volume_ratio >= self.volume_increase_threshold,
                volume_ratio <= self.volume_decrease_threshold)
    
    def analyze_stock(self, symbol, data):
        """Analyze a stock for volatility and patterns"""
        if symbol not in self.top_stocks or not data or len(data) < self.pattern_lookback:
            return None
        
        # Extract price and volume data
        prices = [d['close'] for d in data]
        volumes = [d['volume'] for d in data]
        
        # Calculate volatility
        volatility = self.calculate_volatility(prices)
        
        # Analyze volume pattern
        volume_increase, volume_decrease = self.analyze_volume_pattern(symbol, volumes)
        
        # Calculate price change
        price_change = (prices[-1] - prices[0]) / prices[0]
        
        return {
            'symbol': symbol,
            'volatility': volatility,
            'volume_increase': volume_increase,
            'volume_decrease': volume_decrease,
            'price_change': price_change,
            'current_price': prices[-1],
            'current_volume': volumes[-1],
            'volume_ratio': volumes[-1] / self.stock_volume_baselines[symbol]
        }
    
    def generate_signals(self, data):
        """Generate trading signals based on volume patterns"""
        signals = []
        
        # First select top volatile stocks if not already selected
        if not self.top_stocks:
            self.select_top_volatile_stocks(data)
            print("\nSelected Top 15 Volatile Stocks:")
            for symbol in self.top_stocks:
                print(f"- {symbol}")
        
        for symbol in self.top_stocks:
            analysis = self.analyze_stock(symbol, data.get(symbol, []))
            if not analysis:
                continue
            
            # Generate signals based on volume patterns
            if analysis['volume_increase']:
                signals.append({
                    'symbol': symbol,
                    'action': 'BUY',
                    'reason': f"Volume increased by {((analysis['volume_ratio'] - 1) * 100):.1f}% above baseline"
                })
            elif analysis['volume_decrease']:
                signals.append({
                    'symbol': symbol,
                    'action': 'SELL',
                    'reason': f"Volume decreased by {((1 - analysis['volume_ratio']) * 100):.1f}% below baseline"
                })
        
        self.signals.extend(signals)
        return signals
    
    def calculate_position_size(self, portfolio, signal):
        """Calculate position size based on portfolio value and risk parameters"""
        if signal['action'] == 'HOLD':
            return 0
        
        # Use 1% of portfolio value per position due to high volatility
        position_value = portfolio.total_value * 0.01
        
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