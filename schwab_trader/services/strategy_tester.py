"""Strategy testing framework with realistic market conditions."""
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from schwab_trader.services.data_manager import DataManager

logger = logging.getLogger(__name__)

class StrategyTester:
    """Simulates trading with realistic market conditions."""
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        commission_per_trade: float = 0.0,  # Schwab's commission
        slippage_percent: float = 0.1,  # 0.1% slippage
        max_position_size: float = 0.2,  # 20% of portfolio per position
        min_position_size: float = 0.05,  # 5% of portfolio per position
        max_leverage: float = 1.0,  # No margin
        risk_free_rate: float = 0.02  # 2% annual risk-free rate
    ):
        """Initialize strategy tester with realistic parameters."""
        self.initial_capital = initial_capital
        self.commission_per_trade = commission_per_trade
        self.slippage_percent = slippage_percent
        self.max_position_size = max_position_size
        self.min_position_size = min_position_size
        self.max_leverage = max_leverage
        self.risk_free_rate = risk_free_rate
        self.data_manager = DataManager()
        
        # Trading state
        self.positions: Dict[str, float] = {}  # symbol -> shares
        self.cash = initial_capital
        self.trades: List[Dict] = []
        self.portfolio_value = initial_capital
        self.daily_returns: List[float] = []
        
    def load_market_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load and prepare market data with realistic conditions."""
        data = self.data_manager.get_historical_data(symbol, start_date, end_date)
        if data is None:
            raise ValueError(f"Could not load data for {symbol}")
        
        # Add realistic market conditions
        data['Spread'] = data['High'] - data['Low']
        data['Volume_MA'] = data['Volume'].rolling(window=20).mean()
        data['Liquidity'] = data['Volume'] / data['Volume_MA']
        
        # Add realistic price impact
        data['Price_Impact'] = np.where(
            data['Liquidity'] < 0.5,
            data['Spread'] * 0.5,  # Higher impact in low liquidity
            data['Spread'] * 0.1   # Lower impact in high liquidity
        )
        
        return data
    
    def calculate_position_size(self, price: float, risk: float) -> int:
        """Calculate realistic position size based on risk."""
        max_position_value = self.portfolio_value * self.max_position_size
        min_position_value = self.portfolio_value * self.min_position_size
        
        # Calculate position size based on risk
        position_value = min(
            max_position_value,
            max(min_position_value, self.portfolio_value * risk)
        )
        
        # Calculate shares (round down to nearest share)
        shares = int(position_value / price)
        return shares
    
    def execute_trade(
        self,
        symbol: str,
        shares: int,
        price: float,
        is_buy: bool,
        timestamp: datetime
    ) -> Tuple[bool, float]:
        """Execute a trade with realistic conditions."""
        # Calculate total cost including slippage and commission
        slippage = price * self.slippage_percent / 100
        execution_price = price + (slippage if is_buy else -slippage)
        total_cost = (execution_price * shares) + self.commission_per_trade
        
        # Check if we have enough cash for buy
        if is_buy and total_cost > self.cash:
            logger.warning(f"Insufficient cash for {symbol} buy: {total_cost} > {self.cash}")
            return False, 0.0
        
        # Update positions and cash
        if is_buy:
            self.positions[symbol] = self.positions.get(symbol, 0) + shares
            self.cash -= total_cost
        else:
            self.positions[symbol] = self.positions.get(symbol, 0) - shares
            self.cash += total_cost
        
        # Record trade
        self.trades.append({
            'timestamp': timestamp,
            'symbol': symbol,
            'shares': shares,
            'price': execution_price,
            'type': 'buy' if is_buy else 'sell',
            'cost': total_cost,
            'slippage': slippage * shares,
            'commission': self.commission_per_trade
        })
        
        return True, execution_price
    
    def calculate_portfolio_value(self, data: pd.DataFrame, timestamp: datetime) -> float:
        """Calculate current portfolio value."""
        position_value = 0.0
        for symbol, shares in self.positions.items():
            if symbol in data.columns:
                price = data.loc[timestamp, symbol]
                position_value += price * shares
        
        return position_value + self.cash
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        returns = pd.Series(self.daily_returns)
        
        # Basic metrics
        total_return = (self.portfolio_value / self.initial_capital) - 1
        annual_return = (1 + total_return) ** (252 / len(returns)) - 1
        
        # Risk metrics
        volatility = returns.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - self.risk_free_rate) / volatility
        
        # Trade metrics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t['type'] == 'buy' and t['price'] < self.portfolio_value])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'max_drawdown': (returns.cumsum().expanding().max() - returns.cumsum()).max(),
            'avg_trade_return': np.mean([t['price'] / t['cost'] - 1 for t in self.trades]) if self.trades else 0
        }
    
    def run_strategy(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        strategy_func: callable
    ) -> Dict:
        """Run a strategy with realistic market conditions."""
        # Load and prepare data
        data = self.load_market_data(symbol, start_date, end_date)
        
        # Run strategy for each day
        for timestamp in data.index:
            # Get current portfolio value
            current_value = self.calculate_portfolio_value(data, timestamp)
            self.portfolio_value = current_value
            
            # Get strategy signals
            signals = strategy_func(data, timestamp)
            
            # Execute trades based on signals
            for signal in signals:
                if signal['action'] == 'buy':
                    shares = self.calculate_position_size(
                        data.loc[timestamp, 'Close'],
                        signal.get('risk', 0.1)
                    )
                    success, price = self.execute_trade(
                        symbol,
                        shares,
                        data.loc[timestamp, 'Close'],
                        True,
                        timestamp
                    )
                elif signal['action'] == 'sell':
                    current_shares = self.positions.get(symbol, 0)
                    if current_shares > 0:
                        success, price = self.execute_trade(
                            symbol,
                            current_shares,
                            data.loc[timestamp, 'Close'],
                            False,
                            timestamp
                        )
            
            # Record daily return
            daily_return = (current_value / self.portfolio_value) - 1
            self.daily_returns.append(daily_return)
        
        # Calculate final metrics
        metrics = self.calculate_metrics()
        
        return {
            'metrics': metrics,
            'trades': self.trades,
            'final_portfolio_value': self.portfolio_value,
            'daily_returns': self.daily_returns
        } 