import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Callable, Any
from schwab_trader.utils.schwab_oauth import SchwabOAuth
import pytz

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class StrategyTester:
    def __init__(self):
        self.schwab = None
        self.token = None
        self.positions = {}
        self.cash_balance = 0
        self.initial_balance = 0
        self.trade_history = []
        self.market_timezone = pytz.timezone('America/New_York')
        self.volume_monitoring = {}  # Track volume data for each position
        self.budget = 0
        self.active_positions = {}
        self.running = False
        self.last_balance_check = 0
        self.profit_loss_threshold = 500  # $500 threshold for detailed summaries
        
    def is_market_open(self) -> bool:
        """Check if the market is currently open"""
        now = datetime.now(self.market_timezone)
        # Market hours: 9:30 AM to 4:00 PM ET
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if it's a weekday
        if now.weekday() >= 5:  # 5 is Saturday, 6 is Sunday
            return False
            
        return market_open <= now <= market_close
        
    def is_near_market_close(self, minutes_before: int = 20) -> bool:
        """Check if we're within X minutes of market close"""
        now = datetime.now(self.market_timezone)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        time_to_close = market_close - now
        
        return 0 < time_to_close.total_seconds() <= (minutes_before * 60)
        
    def auto_sell_before_close(self) -> Dict[str, Any]:
        """Automatically sell all positions 20 minutes before market close"""
        if not self.is_near_market_close():
            return {'status': 'not_time', 'message': 'Not within 20 minutes of market close'}
            
        if not self.active_positions:
            return {'status': 'no_positions', 'message': 'No positions to sell'}
            
        results = {
            'trades': [],
            'total_profit': 0,
            'positions_closed': []
        }
        
        for symbol, position in list(self.active_positions.items()):
            try:
                # Get current price
                stock = yf.Ticker(symbol)
                current_price = stock.history(period='1d')['Close'].iloc[-1]
                
                # Calculate profit/loss
                profit = (current_price - position['entry_price']) * position['shares']
                
                # Record the trade
                trade = {
                    'type': 'SELL',
                    'symbol': symbol,
                    'price': current_price,
                    'quantity': position['shares'],
                    'timestamp': datetime.now().isoformat(),
                    'profit': profit
                }
                
                # Update cash balance
                self.cash_balance += position['shares'] * current_price
                
                # Remove position
                del self.active_positions[symbol]
                
                # Record results
                results['trades'].append(trade)
                results['total_profit'] += profit
                results['positions_closed'].append(symbol)
                
                logger.info(f"Auto-sold {symbol}: {position['shares']} shares at ${current_price:.2f}")
                
            except Exception as e:
                logger.error(f"Error auto-selling {symbol}: {str(e)}")
                continue
                
        return results
        
    def update_volume_monitoring(self, symbol: str) -> Dict:
        """Update volume monitoring data for a position"""
        try:
            stock = yf.Ticker(symbol)
            # Get last 5 days of data for volume analysis
            data = stock.history(period="5d", interval="1d")
            
            if data.empty:
                return {}
                
            # Calculate volume metrics
            current_volume = data['Volume'].iloc[-1]
            avg_volume = data['Volume'].mean()
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Update volume monitoring data
            self.volume_monitoring[symbol] = {
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'volume_ratio': volume_ratio,
                'last_updated': datetime.now(self.market_timezone),
                'volume_history': data['Volume'].to_dict()
            }
            
            return self.volume_monitoring[symbol]
            
        except Exception as e:
            logger.error(f"Error updating volume monitoring for {symbol}: {str(e)}")
            return {}
            
    def get_volume_alerts(self, symbol: str) -> List[str]:
        """Get alerts based on volume patterns"""
        alerts = []
        if symbol not in self.volume_monitoring:
            return alerts
            
        volume_data = self.volume_monitoring[symbol]
        
        # Check for unusual volume
        if volume_data['volume_ratio'] > 2.0:
            alerts.append(f"High volume alert: {symbol} trading at {volume_data['volume_ratio']:.2f}x average volume")
        elif volume_data['volume_ratio'] < 0.5:
            alerts.append(f"Low volume alert: {symbol} trading at {volume_data['volume_ratio']:.2f}x average volume")
            
        return alerts
        
    def run_auto_trading(self, strategy: Callable, symbols: List[str], check_interval: int = 60) -> None:
        """
        Run auto trading with automatic position closing before market close
        """
        import time
        
        self.running = True
        self.last_balance_check = self.get_current_balance()
        logger.info(f"Starting auto trading with strategy {strategy.__name__} on symbols {symbols}")
        
        while self.running:
            try:
                # Check for significant profit/loss changes
                self.check_profit_loss()
                
                # Check if market is open
                if not self.is_market_open():
                    logger.info("Market is closed, waiting...")
                    time.sleep(300)  # Check every 5 minutes when market is closed
                    continue
                    
                # Check if we need to auto-sell
                if self.is_near_market_close():
                    logger.info("Near market close, auto-selling positions...")
                    results = self.auto_sell_before_close()
                    logger.info(f"Auto-sell results: {results}")
                    
                # Update volume monitoring for all held positions
                for symbol in self.positions:
                    volume_data = self.update_volume_monitoring(symbol)
                    alerts = self.get_volume_alerts(symbol)
                    for alert in alerts:
                        logger.info(alert)
                    
                # Run normal trading strategy
                for symbol in symbols:
                    try:
                        stock = yf.Ticker(symbol)
                        data = stock.history(period="1mo", interval="1d")
                        if not data.empty:
                            data = self.calculate_indicators(data)
                            signal = strategy(data)
                            
                            if signal == 'BUY' and symbol not in self.positions:
                                # Buy logic here
                                pass
                            elif signal == 'SELL' and symbol in self.positions:
                                # Sell logic here
                                pass
                                
                    except Exception as e:
                        logger.error(f"Error trading {symbol}: {str(e)}")
                        continue
                        
                # Wait for next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in auto trading loop: {str(e)}")
                time.sleep(check_interval)
                continue
        
    def sync_with_schwab(self, token: Dict):
        """Sync with Schwab account for paper trading"""
        self.token = token
        self.schwab = SchwabOAuth()
        self.schwab.token = token
        
        # Get account data
        account_data = self.schwab.get_accounts(token)
        if account_data:
            account = account_data.get('securitiesAccount', {})
            current_balances = account.get('currentBalances', {})
            self.cash_balance = current_balances.get('cashBalance', 0)
            self.initial_balance = self.cash_balance
            
            # Get current positions
            positions = self.schwab.get_positions(token)
            for position in positions:
                symbol = position.get('symbol')
                if symbol:
                    self.positions[symbol] = {
                        'quantity': position.get('quantity', 0),
                        'average_price': position.get('averagePrice', 0)
                    }
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str, interval: str = '1d') -> pd.DataFrame:
        """Get historical data for a symbol"""
        try:
            stock = yf.Ticker(symbol)
            data = stock.history(start=start_date, end=end_date, interval=interval)
            return data
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return pd.DataFrame()
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate common technical indicators"""
        # Simple Moving Averages
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        
        # RSI
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        data['BB_middle'] = data['Close'].rolling(window=20).mean()
        data['BB_std'] = data['Close'].rolling(window=20).std()
        data['BB_upper'] = data['BB_middle'] + (data['BB_std'] * 2)
        data['BB_lower'] = data['BB_middle'] - (data['BB_std'] * 2)
        
        # MACD
        exp1 = data['Close'].ewm(span=12, adjust=False).mean()
        exp2 = data['Close'].ewm(span=26, adjust=False).mean()
        data['MACD'] = exp1 - exp2
        data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
        
        return data
    
    def backtest_strategy(self, 
                         strategy: Callable, 
                         symbols: List[str], 
                         start_date: str, 
                         end_date: str,
                         initial_capital: float = 100000) -> Dict[str, Any]:
        """Backtest a trading strategy"""
        results = {
            'trades': [],
            'portfolio_value': [],
            'returns': [],
            'metrics': {}
        }
        
        # Initialize portfolio
        portfolio = {
            'cash': initial_capital,
            'positions': {},
            'value': initial_capital
        }
        
        # Get historical data for all symbols
        historical_data = {}
        for symbol in symbols:
            data = self.get_historical_data(symbol, start_date, end_date)
            if not data.empty:
                data = self.calculate_indicators(data)
                historical_data[symbol] = data
        
        # Run strategy on each day
        for date in pd.date_range(start=start_date, end=end_date):
            if date.weekday() >= 5:  # Skip weekends
                continue
                
            daily_portfolio_value = portfolio['cash']
            
            # Update positions value
            for symbol, position in portfolio['positions'].items():
                if date in historical_data[symbol].index:
                    price = historical_data[symbol].loc[date, 'Close']
                    daily_portfolio_value += position['quantity'] * price
            
            # Run strategy
            for symbol in symbols:
                if symbol in historical_data and date in historical_data[symbol].index:
                    data = historical_data[symbol].loc[:date]
                    signal = strategy(data)
                    
                    if signal == 'BUY' and symbol not in portfolio['positions']:
                        # Buy signal
                        price = historical_data[symbol].loc[date, 'Close']
                        quantity = int(portfolio['cash'] * 0.1 / price)  # Use 10% of cash
                        if quantity > 0:
                            portfolio['positions'][symbol] = {
                                'quantity': quantity,
                                'entry_price': price
                            }
                            portfolio['cash'] -= quantity * price
                            results['trades'].append({
                                'date': date,
                                'symbol': symbol,
                                'action': 'BUY',
                                'quantity': quantity,
                                'price': price
                            })
                    
                    elif signal == 'SELL' and symbol in portfolio['positions']:
                        # Sell signal
                        position = portfolio['positions'][symbol]
                        price = historical_data[symbol].loc[date, 'Close']
                        portfolio['cash'] += position['quantity'] * price
                        results['trades'].append({
                            'date': date,
                            'symbol': symbol,
                            'action': 'SELL',
                            'quantity': position['quantity'],
                            'price': price,
                            'profit': (price - position['entry_price']) * position['quantity']
                        })
                        del portfolio['positions'][symbol]
            
            results['portfolio_value'].append(daily_portfolio_value)
        
        # Calculate metrics
        returns = pd.Series(results['portfolio_value']).pct_change()
        results['metrics'] = {
            'total_return': (results['portfolio_value'][-1] / initial_capital - 1) * 100,
            'sharpe_ratio': np.sqrt(252) * returns.mean() / returns.std() if len(returns) > 1 else 0,
            'max_drawdown': (pd.Series(results['portfolio_value']).cummax() - pd.Series(results['portfolio_value'])) / pd.Series(results['portfolio_value']).cummax() * 100,
            'num_trades': len(results['trades'])
        }
        
        return results
    
    def paper_trade(self, strategy: Callable, symbols: List[str]) -> Dict[str, Any]:
        """Run paper trading with real-time data"""
        if not self.schwab or not self.token:
            raise ValueError("Must sync with Schwab account first")
        
        results = {
            'trades': [],
            'portfolio_value': [],
            'positions': self.positions.copy(),
            'cash_balance': self.cash_balance
        }
        
        # Get current market data
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                data = stock.history(period="1mo", interval="1d")
                if not data.empty:
                    data = self.calculate_indicators(data)
                    
                    # Run strategy
                    signal = strategy(data)
                    
                    if signal == 'BUY' and symbol not in self.positions:
                        # Simulate buy
                        price = data['Close'].iloc[-1]
                        quantity = int(self.cash_balance * 0.1 / price)  # Use 10% of cash
                        if quantity > 0:
                            self.positions[symbol] = {
                                'quantity': quantity,
                                'average_price': price
                            }
                            self.cash_balance -= quantity * price
                            results['trades'].append({
                                'date': datetime.now(),
                                'symbol': symbol,
                                'action': 'BUY',
                                'quantity': quantity,
                                'price': price
                            })
                    
                    elif signal == 'SELL' and symbol in self.positions:
                        # Simulate sell
                        position = self.positions[symbol]
                        price = data['Close'].iloc[-1]
                        self.cash_balance += position['quantity'] * price
                        results['trades'].append({
                            'date': datetime.now(),
                            'symbol': symbol,
                            'action': 'SELL',
                            'quantity': position['quantity'],
                            'price': price,
                            'profit': (price - position['average_price']) * position['quantity']
                        })
                        del self.positions[symbol]
            
            except Exception as e:
                logger.error(f"Error paper trading {symbol}: {str(e)}")
        
        # Calculate current portfolio value
        portfolio_value = self.cash_balance
        for symbol, position in self.positions.items():
            try:
                stock = yf.Ticker(symbol)
                price = stock.info.get('regularMarketPrice', 0)
                portfolio_value += position['quantity'] * price
            except Exception as e:
                logger.error(f"Error getting price for {symbol}: {str(e)}")
        
        results['portfolio_value'] = portfolio_value
        results['positions'] = self.positions
        results['cash_balance'] = self.cash_balance
        
        return results

    def set_budget(self, budget):
        """Set the trading budget"""
        self.budget = budget
        logger.info(f"Set trading budget to ${budget}")
        
    def get_current_balance(self):
        """Get current account balance including positions"""
        total_value = self.cash_balance
        
        for symbol, position in self.active_positions.items():
            try:
                stock = yf.Ticker(symbol)
                current_price = stock.info.get('regularMarketPrice', 0)
                total_value += position['shares'] * current_price
            except Exception as e:
                logger.error(f"Error getting current price for {symbol}: {str(e)}")
                
        return total_value
        
    def get_active_positions(self):
        """Get current active positions"""
        return self.active_positions
        
    def get_trade_history(self):
        """Get trade history"""
        return self.trade_history
    
    def check_profit_loss(self):
        """Check for significant profit/loss changes and generate detailed summary"""
        current_balance = self.get_current_balance()
        change = current_balance - self.last_balance_check
        
        if abs(change) >= self.profit_loss_threshold:
            summary = self.generate_profit_loss_summary(change)
            logger.info(f"\n{'='*50}\nSignificant Balance Change: ${change:.2f}\n{summary}\n{'='*50}")
            self.last_balance_check = current_balance
            
    def generate_profit_loss_summary(self, change):
        """Generate detailed summary of profit/loss causes"""
        summary = []
        
        # Add current positions and their performance
        summary.append("\nCurrent Positions:")
        for symbol, position in self.active_positions.items():
            try:
                stock = yf.Ticker(symbol)
                current_price = stock.info.get('regularMarketPrice', 0)
                position_value = position['shares'] * current_price
                position_pnl = (current_price - position['entry_price']) * position['shares']
                
                # Get recent trading decision details
                data = stock.history(period="30d")
                if not data.empty:
                    signal, decision_details = self.strategy(data)
                    summary.append(f"{symbol}: {position['shares']} shares @ ${current_price:.2f} (P/L: ${position_pnl:.2f})")
                    summary.append(f"  Last Decision: {decision_details['reason']}")
                    summary.append(f"  Volume Ratio: {decision_details['current_volume_ratio']:.2f}")
                    summary.append(f"  Up Volume: {decision_details['up_volume']:.0f}")
                    summary.append(f"  Down Volume: {decision_details['down_volume']:.0f}")
            except Exception as e:
                logger.error(f"Error getting position data for {symbol}: {str(e)}")
        
        # Add recent trade history with decision details
        summary.append("\nRecent Trades:")
        recent_trades = self.trade_history[-5:]  # Last 5 trades
        for trade in recent_trades:
            try:
                stock = yf.Ticker(trade['symbol'])
                data = stock.history(period="30d", start=trade['timestamp'])
                if not data.empty:
                    signal, decision_details = self.strategy(data)
                    summary.append(f"{trade['type']} {trade['symbol']}: {trade['quantity']} shares @ ${trade['price']:.2f}")
                    summary.append(f"  Decision Reason: {decision_details['reason']}")
                    summary.append(f"  Volume Conditions: Ratio={decision_details['current_volume_ratio']:.2f}")
            except Exception as e:
                logger.error(f"Error analyzing trade {trade['symbol']}: {str(e)}")
        
        return "\n".join(summary) 