from schwab_trader.strategies.volatility_pattern import VolatilityPatternStrategy
from schwab_trader.utils.backtester import StrategyBacktester
from schwab_trader.utils.visualization import TechnicalAnalysisVisualizer
import yfinance as yf
from datetime import datetime, timedelta

def fetch_historical_data(symbols, start_date, end_date):
    """Fetch historical data from Yahoo Finance"""
    data = {}
    for symbol in symbols:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date)
        data[symbol] = df.reset_index().rename(columns={
            'Date': 'date',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }).to_dict('records')
    return data

def main():
    # Initialize strategy
    strategy = VolatilityPatternStrategy(
        volatility_threshold=0.02,
        min_price=10.0,
        min_volume=100000
    )
    
    # Create backtester and visualizer
    backtester = StrategyBacktester(strategy, initial_capital=100000)
    visualizer = TechnicalAnalysisVisualizer(strategy)
    
    # Define test period
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    # Define symbols to test
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    # Fetch historical data
    historical_data = fetch_historical_data(symbols, start_date, end_date)
    
    # Run backtest
    results = backtester.backtest(historical_data)
    
    # Print performance metrics
    print("\nBacktest Results:")
    print(f"Total Return: {results['performance']['total_return']:.2%}")
    print(f"Annualized Return: {results['performance']['annualized_return']:.2%}")
    print(f"Sharpe Ratio: {results['performance']['sharpe_ratio']:.2f}")
    print(f"Maximum Drawdown: {results['performance']['max_drawdown']:.2%}")
    print(f"Win Rate: {results['performance']['win_rate']:.2%}")
    
    # Create and save visualization for each symbol
    for symbol in symbols:
        symbol_data = historical_data[symbol]
        symbol_signals = [t for t in results['trades'] if t['symbol'] == symbol]
        
        chart = visualizer.create_analysis_chart(symbol, symbol_data, symbol_signals)
        visualizer.save_chart(chart, f'charts/{symbol}_analysis.html')
    
    # Create and save overall performance chart
    performance_chart = backtester.plot_results()
    if performance_chart:
        visualizer.save_chart(performance_chart, 'charts/performance.html')

if __name__ == "__main__":
    main()
