import os
import json
import logging
from datetime import datetime
import requests
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/data_collection_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Define market periods
MARKET_PERIODS = {
    'bullish': {
        'start': '2020-04-01',
        'end': '2021-03-31',
        'description': 'Post-COVID Recovery Rally',
        'expected_days': 365
    },
    'bearish': {
        'start': '2022-01-01',
        'end': '2022-12-31',
        'description': '2022 Market Downturn',
        'expected_days': 365
    },
    'neutral': {
        'start': '2021-07-01',
        'end': '2022-06-30',
        'description': '2021-22 Market Consolidation',
        'expected_days': 365
    }
}

# Define stocks to collect with base prices
STOCKS = {
    'TSLA': {
        'name': 'Tesla Inc.',
        'base_price': 180.0
    },
    'NVDA': {
        'name': 'NVIDIA Corporation',
        'base_price': 400.0
    },
    'AMZN': {
        'name': 'Amazon.com Inc.',
        'base_price': 120.0
    },
    'AAPL': {
        'name': 'Apple Inc.',
        'base_price': 170.0
    }
}

def validate_data(data, symbol, market_condition):
    """Validate the collected data for completeness and consistency."""
    try:
        # Check required fields
        required_fields = ['prices', 'trades', 'market_condition', 'symbol', 'period']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate prices data
        prices = data['prices']
        if len(prices) != MARKET_PERIODS[market_condition]['expected_days']:
            raise ValueError(f"Expected {MARKET_PERIODS[market_condition]['expected_days']} days of data, got {len(prices)}")
        
        # Check price data structure
        for price in prices:
            required_price_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
            for field in required_price_fields:
                if field not in price:
                    raise ValueError(f"Missing price field: {field}")
        
        # Validate trades data
        trades = data['trades']
        for trade in trades:
            required_trade_fields = ['date', 'type', 'price', 'volume']
            for field in required_trade_fields:
                if field not in trade:
                    raise ValueError(f"Missing trade field: {field}")
        
        # Calculate and log statistics
        stats = {
            'price_range': {
                'min': min(p['low'] for p in prices),
                'max': max(p['high'] for p in prices),
                'avg': sum(p['close'] for p in prices) / len(prices)
            },
            'volume_stats': {
                'total': sum(p['volume'] for p in prices),
                'avg': sum(p['volume'] for p in prices) / len(prices),
                'max': max(p['volume'] for p in prices)
            },
            'trade_stats': {
                'total': len(trades),
                'buy_count': sum(1 for t in trades if t['type'] == 'buy'),
                'sell_count': sum(1 for t in trades if t['type'] == 'sell')
            }
        }
        
        logger.info(f"Data validation successful for {symbol} ({market_condition})")
        logger.info(f"Price range: ${stats['price_range']['min']:.2f} - ${stats['price_range']['max']:.2f}")
        logger.info(f"Average volume: {stats['volume_stats']['avg']:,.0f}")
        logger.info(f"Total trades: {stats['trade_stats']['total']} (Buy: {stats['trade_stats']['buy_count']}, Sell: {stats['trade_stats']['sell_count']})")
        
        return True, stats
    except Exception as e:
        logger.error(f"Data validation failed for {symbol} ({market_condition}): {str(e)}")
        return False, None

def create_data_directory():
    """Create directory structure for storing historical data."""
    base_dir = Path('data/historical')
    for stock in STOCKS:
        stock_dir = base_dir / stock
        for condition in MARKET_PERIODS:
            period_dir = stock_dir / condition
            period_dir.mkdir(parents=True, exist_ok=True)
    return base_dir

def fetch_historical_data(symbol, market_condition):
    """Fetch historical data for a symbol and market condition."""
    try:
        response = requests.get(f'http://localhost:5000/dashboard/api/test_data/{symbol}/{market_condition}')
        if not response.ok:
            raise Exception(f"API request failed: {response.status_code}")
        
        data = response.json()
        if data['status'] != 'success':
            raise Exception(f"API returned error: {data.get('message', 'Unknown error')}")
        
        # Validate the data
        is_valid, stats = validate_data(data['data'], symbol, market_condition)
        if not is_valid:
            raise Exception("Data validation failed")
        
        # Add validation stats to the data
        data['data']['validation_stats'] = stats
        return data['data']
    except Exception as e:
        logger.error(f"Error fetching data for {symbol} ({market_condition}): {str(e)}")
        return None

def save_historical_data(data, symbol, market_condition, base_dir):
    """Save historical data to JSON file."""
    try:
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{symbol}_{market_condition}_{timestamp}.json"
        filepath = base_dir / symbol / market_condition / filename
        
        # Save the data
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved data to {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"Error saving data for {symbol} ({market_condition}): {str(e)}")
        return None

def collect_all_data():
    """Collect historical data for all stocks and market conditions."""
    base_dir = create_data_directory()
    results = {
        'successful': [],
        'failed': []
    }
    
    for symbol, stock_info in STOCKS.items():
        logger.info(f"\n{'='*50}")
        logger.info(f"Collecting data for {symbol} ({stock_info['name']})")
        logger.info(f"{'='*50}")
        
        for condition, period in MARKET_PERIODS.items():
            logger.info(f"\nCollecting {condition} market data ({period['description']})")
            logger.info(f"Period: {period['start']} to {period['end']}")
            
            data = fetch_historical_data(symbol, condition)
            if data:
                filepath = save_historical_data(data, symbol, condition, base_dir)
                if filepath:
                    results['successful'].append({
                        'symbol': symbol,
                        'condition': condition,
                        'filepath': str(filepath),
                        'stats': data['validation_stats']
                    })
                    logger.info(f"Successfully collected and saved {condition} data for {symbol}")
                else:
                    results['failed'].append({
                        'symbol': symbol,
                        'condition': condition,
                        'error': 'Failed to save data'
                    })
            else:
                results['failed'].append({
                    'symbol': symbol,
                    'condition': condition,
                    'error': 'Failed to fetch data'
                })
    
    # Save collection summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'total_collected': len(results['successful']),
        'total_failed': len(results['failed']),
        'successful': results['successful'],
        'failed': results['failed']
    }
    
    summary_file = base_dir / 'collection_summary.json'
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"\nCollection Summary:")
    logger.info(f"Total successful: {len(results['successful'])}")
    logger.info(f"Total failed: {len(results['failed'])}")
    logger.info(f"Summary saved to {summary_file}")

if __name__ == '__main__':
    collect_all_data() 