"""Script to gather and validate historical data for strategy testing."""
import logging
import os
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask
from schwab_trader.services.data_manager import DataManager
from schwab_trader.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Create Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(Config)
    return app

def ensure_data_directory():
    """Create data directory structure if it doesn't exist."""
    directories = [
        'data/raw',
        'data/processed',
        'data/validation',
        'data/periods'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

def validate_data(data: pd.DataFrame, symbol: str) -> bool:
    """Validate the quality of the data."""
    if data is None or data.empty:
        logger.error(f"No data available for {symbol}")
        return False
    
    # Check for missing values
    missing_values = data.isnull().sum()
    if missing_values.any():
        logger.warning(f"Missing values in {symbol} data:\n{missing_values[missing_values > 0]}")
        return False
    
    # Check for data consistency
    required_columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in data.columns for col in required_columns):
        logger.error(f"Missing required columns in {symbol} data")
        return False
    
    # Check for data quality
    if (data['High'] < data['Low']).any():
        logger.error(f"Invalid price data in {symbol} (High < Low)")
        return False
    
    if (data['Volume'] < 0).any():
        logger.error(f"Invalid volume data in {symbol} (negative volume)")
        return False
    
    return True

def save_data(data: pd.DataFrame, symbol: str, period_type: str, start_date: datetime, end_date: datetime):
    """Save data to appropriate location."""
    filename = f"data/periods/{symbol}_{period_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
    data.to_csv(filename)
    logger.info(f"Saved {period_type} data for {symbol} to {filename}")

def main():
    """Main function to gather and validate historical data."""
    # Create Flask application
    app = create_app()
    
    # Ensure data directories exist
    ensure_data_directory()
    
    symbols = ['TSLA', 'NVDA', 'AAPL']
    
    # Run within application context
    with app.app_context():
        data_manager = DataManager()
        
        # Define time periods
        end_date = datetime.now()
        start_date = end_date - timedelta(days=20*365)  # 20 years
        
        # Gather and validate data for each symbol
        for symbol in symbols:
            logger.info(f"\nProcessing {symbol}...")
            
            # Get full historical data
            logger.info("Fetching full historical data...")
            full_data = data_manager.get_historical_data(symbol, start_date, end_date)
            
            if not validate_data(full_data, symbol):
                logger.error(f"Skipping {symbol} due to data validation issues")
                continue
            
            # Save raw data
            full_data.to_csv(f"data/raw/{symbol}_full.csv")
            
            # Analyze and save different market periods
            periods = data_manager.analyze_market_periods([symbol], years=20)
            
            for period_type, period_data in periods[symbol].items():
                logger.info(f"\nProcessing {period_type} period for {symbol}...")
                
                # Get data for specific period
                period_start = period_data['start_date']
                period_end = period_data['end_date']
                
                period_specific_data = data_manager.get_historical_data(
                    symbol,
                    period_start,
                    period_end
                )
                
                if validate_data(period_specific_data, symbol):
                    save_data(period_specific_data, symbol, period_type, period_start, period_end)
                else:
                    logger.error(f"Failed to validate {period_type} period data for {symbol}")
            
            # Generate validation report
            validation_report = {
                'symbol': symbol,
                'total_days': len(full_data),
                'date_range': f"{full_data.index[0]} to {full_data.index[-1]}",
                'avg_daily_volume': full_data['Volume'].mean(),
                'avg_daily_range': (full_data['High'] - full_data['Low']).mean(),
                'data_quality': 'Valid' if validate_data(full_data, symbol) else 'Invalid'
            }
            
            # Save validation report
            pd.DataFrame([validation_report]).to_csv(f"data/validation/{symbol}_validation.csv")
            logger.info(f"Saved validation report for {symbol}")

if __name__ == "__main__":
    main() 