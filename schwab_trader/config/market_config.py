from typing import Dict, Any
from datetime import datetime, timedelta

# Market Periods Configuration
MARKET_PERIODS: Dict[str, Dict[str, Any]] = {
    'bullish': {
        'start': '2020-04-01',
        'end': '2021-03-31',
        'description': 'Post-COVID Recovery Rally',
        'expected_days': 365,
        'price_change_params': {
            'mean': 1.0,  # Average daily price change (%)
            'std': 1.5,   # Standard deviation of price changes
            'min_range': 0.8,  # Minimum price as fraction of base price
            'max_range': 1.5   # Maximum price as fraction of base price
        }
    },
    'bearish': {
        'start': '2022-01-01',
        'end': '2022-12-31',
        'description': '2022 Market Downturn',
        'expected_days': 365,
        'price_change_params': {
            'mean': -1.0,
            'std': 1.5,
            'min_range': 0.5,
            'max_range': 1.2
        }
    },
    'neutral': {
        'start': '2021-07-01',
        'end': '2022-06-30',
        'description': '2021-22 Market Consolidation',
        'expected_days': 365,
        'price_change_params': {
            'mean': 0.0,
            'std': 1.0,
            'min_range': 0.7,
            'max_range': 1.3
        }
    }
}

# Stocks Configuration
STOCKS: Dict[str, Dict[str, Any]] = {
    'TSLA': {
        'name': 'Tesla Inc.',
        'base_price': 180.0,
        'base_volume': 100_000_000,  # Average daily volume
        'sector': 'Consumer Cyclical',
        'industry': 'Auto Manufacturers'
    },
    'NVDA': {
        'name': 'NVIDIA Corporation',
        'base_price': 400.0,
        'base_volume': 50_000_000,
        'sector': 'Technology',
        'industry': 'Semiconductors'
    },
    'AMZN': {
        'name': 'Amazon.com Inc.',
        'base_price': 120.0,
        'base_volume': 30_000_000,
        'sector': 'Consumer Cyclical',
        'industry': 'Internet Retail'
    },
    'AAPL': {
        'name': 'Apple Inc.',
        'base_price': 170.0,
        'base_volume': 80_000_000,
        'sector': 'Technology',
        'industry': 'Consumer Electronics'
    }
}

# Data Collection Configuration
DATA_COLLECTION_CONFIG = {
    'base_url': 'http://localhost:5000/dashboard/api/test_data',
    'retry_attempts': 3,
    'retry_delay': 5,  # seconds
    'timeout': 30,     # seconds
    'batch_size': 100, # number of records to process at once
    'max_workers': 4   # number of parallel workers
}

# Validation Configuration
VALIDATION_CONFIG = {
    'min_price': 0.01,
    'max_price': 10000.0,
    'min_volume': 1,
    'max_volume': 1_000_000_000,
    'required_price_fields': ['date', 'open', 'high', 'low', 'close', 'volume'],
    'required_trade_fields': ['date', 'type', 'price', 'volume'],
    'valid_trade_types': ['buy', 'sell']
}

# Directory Configuration
DIRECTORY_CONFIG = {
    'base_dir': 'data',
    'subdirectories': {
        'raw': 'raw',
        'processed': 'processed',
        'validation': 'validation',
        'periods': 'periods',
        'historical': 'historical',
        'logs': 'logs'
    }
}

def get_market_period_dates(period: str) -> tuple:
    """Get start and end dates for a market period."""
    if period not in MARKET_PERIODS:
        raise ValueError(f"Unknown market period: {period}")
    
    config = MARKET_PERIODS[period]
    return config['start'], config['end']

def get_stock_config(symbol: str) -> dict:
    """Get configuration for a specific stock."""
    if symbol not in STOCKS:
        raise ValueError(f"Unknown stock symbol: {symbol}")
    
    return STOCKS[symbol]

def get_price_change_params(period: str) -> dict:
    """Get price change parameters for a market period."""
    if period not in MARKET_PERIODS:
        raise ValueError(f"Unknown market period: {period}")
    
    return MARKET_PERIODS[period]['price_change_params']

def get_directory_path(directory_type: str) -> str:
    """Get the full path for a specific directory type."""
    if directory_type not in DIRECTORY_CONFIG['subdirectories']:
        raise ValueError(f"Unknown directory type: {directory_type}")
    
    return f"{DIRECTORY_CONFIG['base_dir']}/{DIRECTORY_CONFIG['subdirectories'][directory_type]}" 