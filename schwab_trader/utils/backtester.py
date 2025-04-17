import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import plotly.graph_objects as go

class StrategyBacktester:
    def __init__(self, strategy, initial_capital=100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.results = None
        
    def simulate_portfolio(self):
        """Simulate a portfolio to be used with the strategy"""
        class SimulatedPortfolio:
            def __init__(self, initial_capital):
                self.total_value = initial_capital
                self.cash_value = initial_capital
                self.positions = {}
                
            def update_position(self, symbol, quantity, price):
                if symbol not in self.positions:
                    self.positions[symbol] = {'quantity': 0, 'cost_basis': 0}
                
                self.positions[symbol]['quantity'] += quantity
                if quantity > 0:
                    self.positions[symbol]['cost_basis'] = price
                
                if self.positions[symbol]['quantity'] == 0:
                    del self.positions[symbol]
                
                self.cash_value -= quantity * price
                self.total_value = self.cash_value + sum(
                    pos['quantity'] * price 
                    for pos in self.positions.values()
                )
        
        return SimulatedPortfolio(self.initial_capital)

    def backtest(self, historical_data, start_date=None, end_date=None):
        """Run backtest on historical data"""
        # Initialize results storage
        self.results = {
            'trades': [],
            'portfolio_values': [],
            'metrics': defaultdict(list)
        }
        
        # Convert dates if provided
        if start_date:
            start_date = pd.to_datetime(start_date)
        if end_date:
            end_date = pd.to_datetime(end_date)
        
        # Initialize portfolio
        portfolio = self.simulate_portfolio()
        
        # Process each day
        dates = sorted(list(set(
            d['date'] for data in historical_data.values() 
            for d in data
        )))
        
        for date in dates:
            if start_date and date < start_date:
                continue
            if end_date and date > end_date:
                break
            
            # Prepare daily data
            daily_data = {
                symbol: [d for d in data if d['date'] == date]
                for symbol, data in historical_data.items()
            }
            
            # Generate signals
            signals = self.strategy.generate_signals(daily_data)
            
            # Execute trades
            for signal in signals:
                symbol = signal['symbol']
                price = daily_data[symbol][0]['close']
                
                if signal['action'] == 'BUY':
                    # Calculate position size
                    position_value = self.strategy.calculate_position_size(portfolio, signal)
                    quantity = position_value // price
                    
                    if quantity > 0 and portfolio.cash_value >= quantity * price:
                        portfolio.update_position(symbol, quantity, price)
                        self.results['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'BUY',
                            'quantity': quantity,
                            'price': price,
                            'value': quantity * price,
                            'reason': signal.get('reason', '')
                        })
                
                elif signal['action'] == 'SELL':
                    if symbol in portfolio.positions:
                        quantity = portfolio.positions[symbol]['quantity']
                        portfolio.update_position(symbol, -quantity, price)
                        self.results['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'quantity': quantity,
                            'price': price,
                            'value': quantity * price,
                            'reason': signal.get('reason', '')
                        })
            
            # Record daily portfolio value
            self.results['portfolio_values'].append({
                'date': date,
                'total_value': portfolio.total_value,
                'cash_value': portfolio.cash_value
            })
            
            # Calculate daily metrics
            self._calculate_daily_metrics(date, portfolio)
        
        # Calculate final performance metrics
        self._calculate_performance_metrics()
        
        return self.results

    def _calculate_daily_metrics(self, date, portfolio):
        """Calculate daily performance metrics"""
        self.results['metrics']['dates'].append(date)
        self.results['metrics']['portfolio_value'].append(portfolio.total_value)
        self.results['metrics']['cash_ratio'].append(
            portfolio.cash_value / portfolio.total_value
        )
        
        # Calculate daily returns
        if len(self.results['metrics']['portfolio_value']) > 1:
            daily_return = (
                portfolio.total_value / 
                self.results['metrics']['portfolio_value'][-2] - 1
            )
        else:
            daily_return = 0
        
        self.results['metrics']['daily_returns'].append(daily_return)

    def _calculate_performance_metrics(self):
        """Calculate overall performance metrics"""
        returns = pd.Series(self.results['metrics']['daily_returns'])
        
        self.results['performance'] = {
            'total_return': (
                self.results['metrics']['portfolio_value'][-1] / 
                self.initial_capital - 1
            ),
            'annualized_return': (
                (1 + returns.mean()) ** 252 - 1
                if len(returns) > 0 else 0
            ),
            'sharpe_ratio': (
                np.sqrt(252) * returns.mean() / returns.std()
                if len(returns) > 0 and returns.std() > 0 else 0
            ),
            'max_drawdown': self._calculate_max_drawdown(
                self.results['metrics']['portfolio_value']
            ),
            'win_rate': self._calculate_win_rate(
                self.results['trades']
            )
        }

    def _calculate_max_drawdown(self, portfolio_values):
        """Calculate maximum drawdown"""
        peak = portfolio_values[0]
        max_drawdown = 0
        
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        return max_drawdown

    def _calculate_win_rate(self, trades):
        """Calculate win rate from trades"""
        if not trades:
            return 0
            
        profitable_trades = sum(
            1 for trade in trades
            if trade['action'] == 'SELL' and
            trade['price'] > trade.get('entry_price', 0)
        )
        
        total_trades = sum(
            1 for trade in trades
            if trade['action'] == 'SELL'
        )
        
        return profitable_trades / total_trades if total_trades > 0 else 0

    def plot_results(self, visualizer=None):
        """Plot backtest results"""
        if not self.results:
            return None
            
        # Create performance chart
        df = pd.DataFrame(self.results['portfolio_values'])
        
        fig = go.Figure()
        
        # Add portfolio value line
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['total_value'],
                name='Portfolio Value',
                line=dict(color='blue')
            )
        )
        
        # Add buy/sell markers
        trades_df = pd.DataFrame(self.results['trades'])
        if not trades_df.empty:
            buys = trades_df[trades_df['action'] == 'BUY']
            sells = trades_df[trades_df['action'] == 'SELL']
            
            fig.add_trace(
                go.Scatter(
                    x=buys['date'],
                    y=buys['value'],
                    mode='markers',
                    name='Buy',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color='green'
                    )
                )
            )
            
            fig.add_trace(
                go.Scatter(
                    x=sells['date'],
                    y=sells['value'],
                    mode='markers',
                    name='Sell',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color='red'
                    )
                )
            )
        
        # Update layout
        fig.update_layout(
            title='Backtest Results',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            height=600
        )
        
        return fig
