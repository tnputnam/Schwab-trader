"""Script to analyze market periods and save data for strategy testing."""
import logging
from datetime import datetime
from schwab_trader.services.data_manager import DataManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main function to analyze market periods."""
    symbols = ['TSLA', 'NVDA', 'AAPL']
    data_manager = DataManager()
    
    logger.info("Starting market period analysis...")
    results = data_manager.analyze_market_periods(symbols, years=20)
    
    # Save the actual data for these periods
    for symbol, periods in results.items():
        logger.info(f"\nSaving data for {symbol}:")
        
        # Save bullish period data
        bullish_data = data_manager.get_historical_data(
            symbol,
            periods['bullish']['start_date'],
            periods['bullish']['end_date']
        )
        if bullish_data is not None:
            filename = f"data/{symbol}_bullish_{periods['bullish']['start_date'].strftime('%Y%m%d')}_{periods['bullish']['end_date'].strftime('%Y%m%d')}.csv"
            bullish_data.to_csv(filename)
            logger.info(f"Saved bullish period data to {filename}")
        
        # Save bearish period data
        bearish_data = data_manager.get_historical_data(
            symbol,
            periods['bearish']['start_date'],
            periods['bearish']['end_date']
        )
        if bearish_data is not None:
            filename = f"data/{symbol}_bearish_{periods['bearish']['start_date'].strftime('%Y%m%d')}_{periods['bearish']['end_date'].strftime('%Y%m%d')}.csv"
            bearish_data.to_csv(filename)
            logger.info(f"Saved bearish period data to {filename}")
        
        # Save volatile period data
        volatile_data = data_manager.get_historical_data(
            symbol,
            periods['volatile']['start_date'],
            periods['volatile']['end_date']
        )
        if volatile_data is not None:
            filename = f"data/{symbol}_volatile_{periods['volatile']['start_date'].strftime('%Y%m%d')}_{periods['volatile']['end_date'].strftime('%Y%m%d')}.csv"
            volatile_data.to_csv(filename)
            logger.info(f"Saved volatile period data to {filename}")
    
    logger.info("Analysis complete!")

if __name__ == "__main__":
    main() 