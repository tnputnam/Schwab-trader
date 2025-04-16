from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
import numpy as np

class TradingStrategy(ABC):
    """Base class for trading strategies"""
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.signals = []
        self.performance_history = []
    
    @abstractmethod
    def generate_signals(self, data):
        """Generate trading signals based on strategy rules"""
        pass
    
    def calculate_performance(self, portfolio):
        """Calculate strategy performance metrics"""
        total_value = portfolio.total_value
        cash_value = portfolio.cash_value
        positions_value = total_value - cash_value
        
        # Calculate position metrics
        position_metrics = []
        for position in portfolio.positions:
            metrics = {
                'symbol': position.symbol,
                'quantity': position.quantity,
                'price': position.price,
                'cost_basis': position.cost_basis,
                'market_value': position.market_value,
                'unrealized_gain': position.market_value - position.cost_basis,
                'unrealized_gain_percent': ((position.market_value - position.cost_basis) / position.cost_basis) * 100,
                'day_change': position.day_change_dollar,
                'day_change_percent': position.day_change_percent
            }
            position_metrics.append(metrics)
        
        # Calculate portfolio metrics
        portfolio_metrics = {
            'total_value': total_value,
            'cash_value': cash_value,
            'positions_value': positions_value,
            'cash_percentage': (cash_value / total_value) * 100,
            'positions_percentage': (positions_value / total_value) * 100,
            'total_gain': portfolio.total_gain,
            'total_gain_percent': portfolio.total_gain_percent,
            'day_change': portfolio.day_change,
            'day_change_percent': portfolio.day_change_percent,
            'timestamp': datetime.now(),
            'positions': position_metrics
        }
        
        self.performance_history.append(portfolio_metrics)
        return portfolio_metrics
    
    def get_performance_summary(self):
        """Get summary of strategy performance"""
        if not self.performance_history:
            return None
        
        latest = self.performance_history[-1]
        return {
            'strategy_name': self.name,
            'total_value': latest['total_value'],
            'total_gain': latest['total_gain'],
            'total_gain_percent': latest['total_gain_percent'],
            'day_change': latest['day_change'],
            'day_change_percent': latest['day_change_percent'],
            'cash_percentage': latest['cash_percentage'],
            'positions_percentage': latest['positions_percentage'],
            'timestamp': latest['timestamp']
        }
    
    def get_position_summary(self):
        """Get summary of current positions"""
        if not self.performance_history:
            return None
        
        latest = self.performance_history[-1]
        return latest['positions'] 