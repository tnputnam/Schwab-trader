from schwab_trader.testing.auto_trade_test import MockAlphaVantageAPI, AutoTradeTest
from schwab_trader.strategies.sentiment_volume import SentimentVolumeStrategy
from schwab_trader.database import db
import pandas as pd
import time
from datetime import datetime, timedelta
import numpy as np

def generate_mock_news_data(symbol):
    """Generate mock news data with sentiment"""
    positive_news = [
        f"{symbol} reports strong earnings growth",
        f"Analysts upgrade {symbol} to buy rating",
        f"{symbol} announces new product launch"
    ]
    negative_news = [
        f"{symbol} misses earnings expectations",
        f"Analysts downgrade {symbol} rating",
        f"{symbol} faces regulatory challenges"
    ]
    return positive_news + negative_news

def generate_mock_volume_data():
    """Generate mock volume data with baseline and spikes"""
    base_volume = 100000
    volume_data = []
    
    # Generate 30 days of baseline volume
    for _ in range(30):
        # Add some random variation to baseline
        volume = base_volume * (1 + np.random.normal(0, 0.1))  # 10% random variation
        volume_data.append(volume)
    
    # Add volume spikes
    for i in range(10):
        if i % 3 == 0:
            # Simulate 15%+ volume increase
            volume = base_volume * 1.2  # 20% increase
        else:
            # Return to baseline
            volume = base_volume * (1 + np.random.normal(0, 0.1))
        volume_data.append(volume)
    
    return volume_data

def run_sentiment_volume_test():
    # Initialize test environment
    test_env = AutoTradeTest()
    test_env.setUp()
    
    try:
        # Initialize strategy with custom parameters
        strategy = SentimentVolumeStrategy(
            volume_increase_threshold=1.15,  # 15% increase from baseline
            min_volume=100000,
            lookback_days=30
        )
        
        # Run simulation for 10 iterations
        for i in range(10):
            print(f"\nIteration {i+1}")
            print("=" * 50)
            
            # Update portfolio data
            test_env.test_portfolio_update()
            
            # Get current portfolio state
            portfolio_data = strategy.calculate_performance(test_env.test_portfolio)
            
            # Add mock news and volume data
            for position in portfolio_data['positions']:
                position['news'] = generate_mock_news_data(position['symbol'])
                position['volume_history'] = generate_mock_volume_data()
            
            # Generate trading signals
            signals = strategy.generate_signals(portfolio_data)
            
            # Execute trades
            trades = strategy.execute_trades(test_env.test_portfolio, signals)
            
            # Print results
            print("\nPortfolio Summary:")
            summary = strategy.get_performance_summary()
            for key, value in summary.items():
                if isinstance(value, (int, float)):
                    print(f"{key}: {value:.2f}")
                else:
                    print(f"{key}: {value}")
            
            print("\nTrading Signals:")
            for signal in signals:
                print(f"{signal['symbol']}: {signal['action']} - {signal['reason']}")
            
            print("\nExecuted Trades:")
            for trade in trades:
                print(f"{trade['symbol']}: {trade['action']} ${trade['size']:.2f} - {trade['reason']}")
            
            # Wait before next iteration
            time.sleep(1)
    
    finally:
        # Clean up test environment
        test_env.tearDown()

if __name__ == '__main__':
    run_sentiment_volume_test() 