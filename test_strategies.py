from strategy_tester import StrategyTester
from example_strategies import (
    moving_average_crossover_strategy,
    rsi_strategy,
    bollinger_bands_strategy
)
from datetime import datetime, timedelta
import pandas as pd

def main():
    # Define test parameters
    symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL']  # Example symbols
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Test Moving Average Crossover Strategy
    print("\nTesting Moving Average Crossover Strategy...")
    ma_tester = StrategyTester()
    ma_results = ma_tester.run_strategy(
        moving_average_crossover_strategy,
        symbols,
        start_date,
        end_date
    )
    print(f"Total Return: {ma_results['total_return']:.2%}")
    print(f"Sharpe Ratio: {ma_results['sharpe_ratio']:.2f}")
    
    # Test RSI Strategy
    print("\nTesting RSI Strategy...")
    rsi_tester = StrategyTester()
    rsi_results = rsi_tester.run_strategy(
        rsi_strategy,
        symbols,
        start_date,
        end_date
    )
    print(f"Total Return: {rsi_results['total_return']:.2%}")
    print(f"Sharpe Ratio: {rsi_results['sharpe_ratio']:.2f}")
    
    # Test Bollinger Bands Strategy
    print("\nTesting Bollinger Bands Strategy...")
    bb_tester = StrategyTester()
    bb_results = bb_tester.run_strategy(
        bollinger_bands_strategy,
        symbols,
        start_date,
        end_date
    )
    print(f"Total Return: {bb_results['total_return']:.2%}")
    print(f"Sharpe Ratio: {bb_results['sharpe_ratio']:.2f}")
    
    # Compare strategies
    print("\nStrategy Comparison:")
    print(f"{'Strategy':<30} {'Total Return':<15} {'Sharpe Ratio':<15}")
    print("-" * 60)
    print(f"{'Moving Average Crossover':<30} {ma_results['total_return']:.2%:<15} {ma_results['sharpe_ratio']:.2f:<15}")
    print(f"{'RSI':<30} {rsi_results['total_return']:.2%:<15} {rsi_results['sharpe_ratio']:.2f:<15}")
    print(f"{'Bollinger Bands':<30} {bb_results['total_return']:.2%:<15} {bb_results['sharpe_ratio']:.2f:<15}")

if __name__ == "__main__":
    main() 