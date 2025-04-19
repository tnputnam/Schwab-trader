import requests
import json
import logging
from datetime import datetime

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

def test_data_loading(symbol='TSLA'):
    """Test loading historical data for a symbol."""
    try:
        # Make request to test data endpoint
        response = requests.get(f'http://localhost:5000/dashboard/api/test_data/{symbol}')
        
        if response.status_code == 200:
            data = response.json()
            logger.info(f"Successfully loaded test data for {symbol}")
            logger.info(f"Data points: {len(data['data']['prices'])}")
            logger.info(f"Trade points: {len(data['data']['trades'])}")
            
            # Print sample data
            logger.info("\nSample Price Data:")
            for price in data['data']['prices'][:2]:
                logger.info(f"Date: {price['date']}, Close: {price['close']}, Volume: {price['volume']}")
            
            logger.info("\nTrade Data:")
            for trade in data['data']['trades']:
                logger.info(f"Date: {trade['date']}, Type: {trade['type']}, Price: {trade['price']}")
                
            return True
        else:
            logger.error(f"Failed to load data: {response.status_code}")
            logger.error(response.text)
            return False
            
    except Exception as e:
        logger.error(f"Error testing data loading: {str(e)}")
        return False

if __name__ == '__main__':
    test_data_loading() 