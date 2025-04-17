from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import json
import requests
from flask import current_app

class StrategyTester:
    def __init__(self, initial_balance: float = 48546.19, cash_balance: float = 65.22):
        self.initial_balance = initial_balance
        self.cash_balance = cash_balance
        self.positions: Dict[str, Dict] = {}  # symbol -> {quantity, avg_price}
        self.trade_history: List[Dict] = []
        self.performance_history: List[Dict] = []
        
    def add_position(self, symbol: str, quantity: float, avg_price: float):
        """Add a position to the test portfolio"""
        self.positions[symbol] = {
            'quantity': quantity,
            'avg_price': avg_price
        }
        
    def execute_trade(self, symbol: str, quantity: float, price: float, action: str):
        """Execute a trade and update portfolio"""
        if action == 'buy':
            cost = quantity * price
            if cost > self.cash_balance:
                raise ValueError("Insufficient funds")
            
            if symbol in self.positions:
                # Update existing position
                pos = self.positions[symbol]
                total_cost = (pos['quantity'] * pos['avg_price']) + cost
                pos['quantity'] += quantity
                pos['avg_price'] = total_cost / pos['quantity']
            else:
                # New position
                self.positions[symbol] = {
                    'quantity': quantity,
                    'avg_price': price
                }
            
            self.cash_balance -= cost
            
        elif action == 'sell':
            if symbol not in self.positions:
                raise ValueError(f"No position in {symbol}")
                
            pos = self.positions[symbol]
            if quantity > pos['quantity']:
                raise ValueError("Insufficient shares")
                
            proceeds = quantity * price
            self.cash_balance += proceeds
            
            if quantity == pos['quantity']:
                del self.positions[symbol]
            else:
                pos['quantity'] -= quantity
        
        # Record trade
        self.trade_history.append({
            'timestamp': datetime.now(),
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'action': action
        })
        
    def get_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total_value = self.cash_balance
        for symbol, pos in self.positions.items():
            try:
                current_price = yf.Ticker(symbol).info.get('regularMarketPrice', 0)
                total_value += pos['quantity'] * current_price
            except:
                print(f"Error getting price for {symbol}")
        return total_value
    
    def record_performance(self):
        """Record current portfolio performance"""
        self.performance_history.append({
            'timestamp': datetime.now(),
            'total_value': self.get_portfolio_value(),
            'cash_balance': self.cash_balance,
            'positions': self.positions.copy()
        })
        
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if not self.performance_history:
            return {}
            
        initial_value = self.initial_balance
        current_value = self.get_portfolio_value()
        total_return = (current_value - initial_value) / initial_value
        
        # Calculate daily returns
        daily_returns = []
        for i in range(1, len(self.performance_history)):
            prev_value = self.performance_history[i-1]['total_value']
            curr_value = self.performance_history[i]['total_value']
            daily_return = (curr_value - prev_value) / prev_value
            daily_returns.append(daily_return)
            
        if daily_returns:
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0
            
        return {
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'current_value': current_value,
            'cash_balance': self.cash_balance,
            'positions': self.positions
        }
        
    def run_strategy(self, strategy_func, symbols: List[str], start_date: str, end_date: str):
        """Run a trading strategy on historical data"""
        # Get historical data
        data = {}
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(start=start_date, end=end_date)
                data[symbol] = hist
            except:
                print(f"Error getting data for {symbol}")
                continue
        
        # Run strategy
        for date in pd.date_range(start=start_date, end=end_date):
            date_str = date.strftime('%Y-%m-%d')
            for symbol, df in data.items():
                if date_str in df.index:
                    # Get strategy signals
                    signals = strategy_func(df.loc[:date_str])
                    
                    # Execute trades based on signals
                    if signals.get('action') == 'buy':
                        self.execute_trade(symbol, signals['quantity'], df.loc[date_str]['Close'], 'buy')
                    elif signals.get('action') == 'sell':
                        self.execute_trade(symbol, signals['quantity'], df.loc[date_str]['Close'], 'sell')
                    
            # Record daily performance
            self.record_performance()
            
        return self.get_performance_metrics()

    def sync_with_schwab(self, access_token: str):
        """Sync test portfolio with actual Schwab account"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/json'
        }
        
        # Get current account balances
        response = requests.get(
            'https://api.schwabapi.com/trader/v1/accounts',
            headers=headers
        )
        
        if response.status_code == 200:
            accounts = response.json()
            if accounts and isinstance(accounts, list):
                account = accounts[0]
                current_balances = account.get('securitiesAccount', {}).get('currentBalances', {})
                
                # Update test portfolio with actual values
                self.cash_balance = current_balances.get('cashAvailableForTrading', 0)
                self.initial_balance = current_balances.get('liquidationValue', 0)
                
                # Get positions
                account_number = account.get('securitiesAccount', {}).get('accountNumber')
                if account_number:
                    positions_response = requests.get(
                        f'https://api.schwabapi.com/trader/v1/accounts/{account_number}/positions',
                        headers=headers
                    )
                    
                    if positions_response.status_code == 200:
                        positions = positions_response.json()
                        self.positions = {
                            pos['symbol']: {
                                'quantity': pos['longQuantity'],
                                'avg_price': pos['averagePrice']
                            }
                            for pos in positions
                        } 