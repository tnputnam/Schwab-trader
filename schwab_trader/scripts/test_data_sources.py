import logging
import os
from datetime import datetime, timedelta
from flask import Flask
from schwab_trader.services.schwab_api import SchwabAPI
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
from schwab_trader.services.yfinance import YFinanceAPI
from schwab_trader.services.auth import get_schwab_token

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/test_data_sources_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

def create_app():
    app = Flask(__name__)
    app.config.from_object('schwab_trader.config')
    return app

def test_data_source(symbol, data_source, start_date, end_date):
    """Test a specific data source for a given symbol"""
    try:
        if data_source == 'schwab':
            # First ensure we have a valid token
            token = get_schwab_token()
            if not token:
                logging.error(f"Failed to get Schwab token for {symbol}")
                return False
            
            api = SchwabAPI()
            data = api.get_historical_prices(symbol, start_date, end_date)
        elif data_source == 'alpha_vantage':
            api = AlphaVantageAPI()
            data = api.get_historical_data(symbol, start_date, end_date)
        elif data_source == 'yfinance':
            api = YFinanceAPI()
            data = api.get_historical_data(symbol, start_date, end_date)
        else:
            logging.error(f"Unknown data source: {data_source}")
            return False

        if not data:
            logging.error(f"No data returned from {data_source} for {symbol}")
            return False

        # Log some basic statistics about the data
        logging.info(f"Data from {data_source} for {symbol}:")
        logging.info(f"Number of data points: {len(data)}")
        logging.info(f"Date range: {data[0]['date']} to {data[-1]['date']}")
        logging.info(f"Price range: {min(d['close'] for d in data):.2f} to {max(d['close'] for d in data):.2f}")
        
        return True
    except Exception as e:
        logging.error(f"Error testing {data_source} for {symbol}: {str(e)}")
        return False

def main():
    # Create Flask app context
    app = create_app()
    with app.app_context():
        # Test symbols
        symbols = ['TSLA', 'NVDA', 'AAPL']
        
        # Test date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Test each data source
        data_sources = ['schwab', 'alpha_vantage', 'yfinance']
        
        results = {}
        for symbol in symbols:
            results[symbol] = {}
            for source in data_sources:
                logging.info(f"Testing {source} for {symbol}...")
                success = test_data_source(symbol, source, start_date, end_date)
                results[symbol][source] = success
                logging.info(f"{source} for {symbol}: {'Success' if success else 'Failed'}")
        
        # Print summary
        print("\nTest Results Summary:")
        print("=" * 50)
        for symbol in symbols:
            print(f"\n{symbol}:")
            for source in data_sources:
                status = "✓" if results[symbol][source] else "✗"
                print(f"  {source}: {status}")
            working_sources = sum(1 for source in data_sources if results[symbol][source])
            print(f"  Working sources: {working_sources}/{len(data_sources)}")

if __name__ == "__main__":
    main() 