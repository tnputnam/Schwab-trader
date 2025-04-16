from schwab_trader.testing.auto_trade_test import MockAlphaVantageAPI, TestAutoTrading
from schwab_trader.strategies.momentum import MomentumStrategy
import pandas as pd
import time

def run_momentum_test():
    # Initialize test environment
    test_env = TestAutoTrading()
    test_env.setUp()
    
    # Initialize strategy
    strategy = MomentumStrategy(
        lookback_period=20,
        volume_threshold=1.5,
        price_threshold=0.02
    )
    
    # Run simulation for 10 iterations
    for i in range(10):
        print(f"\nIteration {i+1}")
        print("=" * 50)
        
        # Update portfolio data
        test_env.test_portfolio_update()
        
        # Get current portfolio state
        portfolio_data = strategy.calculate_performance(test_env.test_portfolio)
        
        # Generate trading signals
        signals = strategy.generate_signals(portfolio_data)
        
        # Execute trades
        trades = strategy.execute_trades(test_env.test_portfolio, signals)
        
        # Print results
        print("\nPortfolio Summary:")
        summary = strategy.get_performance_summary()
        for key, value in summary.items():
            if key != 'positions':
                print(f"{key}: {value}")
        
        print("\nTrading Signals:")
        for signal in signals:
            print(f"{signal['symbol']}: {signal['action']} - {signal['reason']}")
        
        print("\nExecuted Trades:")
        for trade in trades:
            print(f"{trade['symbol']}: {trade['action']} ${trade['size']:.2f} - {trade['reason']}")
        
        # Wait before next iteration
        time.sleep(1)

if __name__ == '__main__':
    run_momentum_test() 