import requests
import json
import logging
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/test_data_loader_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_data_loading(symbol, market_condition):
    """Test loading historical data for a symbol with specific market condition."""
    try:
        # Make request to test data endpoint
        response = requests.get(f'http://localhost:5000/dashboard/api/test_data/{symbol}/{market_condition}')
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"\n{'='*50}")
            logger.info(f"Testing {symbol} - {market_condition} market")
            logger.info(f"{'='*50}")
            
            # Log data summary
            prices = data['data']['prices']
            trades = data['data']['trades']
            
            logger.info(f"Data points: {len(prices)}")
            logger.info(f"Trade points: {len(trades)}")
            
            # Calculate and log price statistics
            closes = [p['close'] for p in prices]
            min_price = min(closes)
            max_price = max(closes)
            avg_price = sum(closes) / len(closes)
            
            logger.info(f"Price Range: ${min_price:.2f} - ${max_price:.2f}")
            logger.info(f"Average Price: ${avg_price:.2f}")
            
            # Log trade summary
            buy_trades = len([t for t in trades if t['type'] == 'buy'])
            sell_trades = len([t for t in trades if t['type'] == 'sell'])
            logger.info(f"Buy Trades: {buy_trades}, Sell Trades: {sell_trades}")
            
            # Save data to file
            os.makedirs('test_data', exist_ok=True)
            filename = f'test_data/{symbol}_{market_condition}_{datetime.now().strftime("%Y%m%d")}.json'
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Data saved to {filename}")
            
            return True
        else:
            logger.error(f"Failed to load data: {response.status_code}")
            logger.error(response.text)
            return False
            
    except Exception as e:
        logger.error(f"Error testing data loading: {str(e)}")
        return False

def test_all_conditions():
    """Test all market conditions for all supported stocks."""
    symbols = ['TSLA', 'NVDA', 'AMZN', 'AAPL']
    market_conditions = ['bearish', 'bullish', 'neutral']
    
    for symbol in symbols:
        for condition in market_conditions:
            test_data_loading(symbol, condition)

if __name__ == '__main__':
    test_all_conditions() 