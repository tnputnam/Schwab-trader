from schwab_trader.testing.auto_trade_test import MockAlphaVantageAPI, AutoTradeTest
from schwab_trader.strategies.volatility_pattern import VolatilityPatternStrategy
from schwab_trader.database import db
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

def generate_mock_stock_data(symbol, days=30):
    """Generate mock stock data with volatility and patterns"""
    base_price = np.random.uniform(10, 100)
    base_volume = 100000
    
    data = []
    for i in range(days):
        # Generate price with volatility
        volatility = np.random.uniform(0.01, 0.05)  # 1-5% daily volatility
        price_change = np.random.normal(0, volatility)
        price = base_price * (1 + price_change)
        
        # Generate volume with random variation
        volume = base_volume * np.random.uniform(0.8, 1.2)
        
        data.append({
            'date': datetime.now() - timedelta(days=days-i),
            'open': price * np.random.uniform(0.99, 1.01),
            'high': price * np.random.uniform(1.01, 1.03),
            'low': price * np.random.uniform(0.97, 0.99),
            'close': price,
            'volume': volume
        })
    
    return data

def run_volatility_pattern_test():
    # Initialize test environment
    test_env = AutoTradeTest()
    test_env.setUp()
    
    try:
        # Initialize strategy with custom parameters
        strategy = VolatilityPatternStrategy(
            volatility_threshold=0.02,  # 2% daily volatility
            min_price=5.0,
            min_volume=100000,
            pattern_lookback=20,
            volume_increase_threshold=1.15,  # 15% volume increase
            volume_decrease_threshold=0.85  # 15% volume decrease
        )
        
        # Generate mock stock universe
        stock_universe = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'AMD', 'INTC',
            'META', 'NFLX', 'PYPL', 'ADBE', 'CRM', 'ORCL', 'IBM', 'CSCO',
            'PEP', 'KO', 'JPM', 'BAC', 'WMT', 'HD', 'MCD', 'DIS', 'NKE'
        ]
        stock_data = {symbol: generate_mock_stock_data(symbol) for symbol in stock_universe}
        
        # Run weekly analysis
        print("\nWeekly Volatility Analysis")
        print("=" * 50)
        
        # First run to select top 15 volatile stocks
        strategy.select_top_volatile_stocks(stock_data)
        
        # Monitor selected stocks throughout the week
        for day in range(5):  # 5 trading days
            print(f"\nDay {day + 1} Analysis")
            print("-" * 30)
            
            # Update stock data for the day
            for symbol in strategy.top_stocks:
                new_data = generate_mock_stock_data(symbol, days=1)
                stock_data[symbol].extend(new_data)
                stock_data[symbol] = stock_data[symbol][-30:]  # Keep last 30 days
            
            # Analyze each selected stock
            for symbol in strategy.top_stocks:
                analysis = strategy.analyze_stock(symbol, stock_data[symbol])
                if analysis:
                    print(f"\n{symbol} Analysis:")
                    print(f"Current Price: ${analysis['current_price']:.2f}")
                    print(f"Volatility: {analysis['volatility']:.2%}")
                    print(f"Volume Ratio: {analysis['volume_ratio']:.2f}x baseline")
                    print(f"Price Change: {analysis['price_change']:.2%}")
            
            # Generate trading signals
            signals = strategy.generate_signals(stock_data)
            
            # Execute trades
            trades = strategy.execute_trades(test_env.test_portfolio, signals)
            
            # Print results
            print("\nTrading Signals:")
            for signal in signals:
                print(f"{signal['symbol']}: {signal['action']} - {signal['reason']}")
            
            print("\nExecuted Trades:")
            for trade in trades:
                print(f"{trade['symbol']}: {trade['action']} ${trade['size']:.2f} - {trade['reason']}")
            
            # Wait before next day
            time.sleep(1)
    
    finally:
        # Clean up test environment
        test_env.tearDown()

if __name__ == '__main__':
    run_volatility_pattern_test() 