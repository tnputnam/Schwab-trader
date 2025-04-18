import os
import json
import logging
from datetime import datetime
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import shutil
import psutil
from tqdm import tqdm

from schwab_trader.config.market_config import (
    MARKET_PERIODS,
    STOCKS,
    DATA_COLLECTION_CONFIG,
    get_directory_path
)
from schwab_trader.utils.data_validation import DataValidator

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

class DataCollector:
    def __init__(self):
        self.validator = DataValidator()
        self.base_url = DATA_COLLECTION_CONFIG['base_url']
        self.retry_attempts = DATA_COLLECTION_CONFIG['retry_attempts']
        self.retry_delay = DATA_COLLECTION_CONFIG['retry_delay']
        self.timeout = DATA_COLLECTION_CONFIG['timeout']
        self.batch_size = DATA_COLLECTION_CONFIG['batch_size']
        self.failed_files: List[Path] = []
        self.validation_cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
    
    def check_disk_space(self, required_bytes: int) -> bool:
        """Check if there's enough disk space for data collection."""
        try:
            free_space = psutil.disk_usage('/').free
            return free_space > required_bytes * 2  # Require 2x the space for safety
        except Exception as e:
            logger.error(f"Error checking disk space: {str(e)}")
            return False
    
    def estimate_required_space(self) -> int:
        """Estimate required disk space for data collection."""
        # Rough estimate: 1KB per day per stock * 365 days * number of stocks * number of conditions
        bytes_per_day = 1024
        total_days = sum(period['expected_days'] for period in MARKET_PERIODS.values())
        total_stocks = len(STOCKS)
        return bytes_per_day * total_days * total_stocks
    
    def create_data_directory(self) -> Path:
        """Create directory structure for storing historical data."""
        try:
            required_space = self.estimate_required_space()
            if not self.check_disk_space(required_space):
                raise Exception(f"Insufficient disk space. Required: {required_space/1024/1024:.2f} MB")
            
            base_dir = Path(get_directory_path('historical'))
            for stock in STOCKS:
                stock_dir = base_dir / stock
                for condition in MARKET_PERIODS:
                    period_dir = stock_dir / condition
                    period_dir.mkdir(parents=True, exist_ok=True)
            return base_dir
        except Exception as e:
            logger.error(f"Error creating directory structure: {str(e)}")
            raise
    
    def cleanup_failed_files(self):
        """Remove files from failed data collection attempts."""
        for filepath in self.failed_files:
            try:
                if filepath.exists():
                    filepath.unlink()
                    logger.info(f"Removed failed data file: {filepath}")
            except Exception as e:
                logger.error(f"Error removing failed file {filepath}: {str(e)}")
    
    def validate_input(self, symbol: str, market_condition: str) -> bool:
        """Validate input parameters before processing."""
        if symbol not in STOCKS:
            logger.error(f"Invalid symbol: {symbol}")
            return False
        if market_condition not in MARKET_PERIODS:
            logger.error(f"Invalid market condition: {market_condition}")
            return False
        return True
    
    def fetch_historical_data(self, symbol: str, market_condition: str) -> Optional[Dict[str, Any]]:
        """Fetch historical data for a symbol and market condition with retry logic."""
        if not self.validate_input(symbol, market_condition):
            return None
            
        # Check cache first
        cache_key = (symbol, market_condition)
        if cache_key in self.validation_cache:
            logger.info(f"Using cached validation results for {symbol} ({market_condition})")
            return self.validation_cache[cache_key]
            
        for attempt in range(self.retry_attempts):
            try:
                response = requests.get(
                    f"{self.base_url}/{symbol}/{market_condition}",
                    timeout=self.timeout
                )
                if not response.ok:
                    raise Exception(f"API request failed: {response.status_code}")
                
                data = response.json()
                if data['status'] != 'success':
                    raise Exception(f"API returned error: {data.get('message', 'Unknown error')}")
                
                # Validate the data
                is_valid, stats, message = self.validator.validate_data(
                    data['data'],
                    symbol,
                    market_condition
                )
                
                if not is_valid:
                    raise Exception(f"Data validation failed: {message}")
                
                # Add validation stats to the data
                data['data']['validation_stats'] = stats
                
                # Cache the validated data
                self.validation_cache[cache_key] = data['data']
                return data['data']
                
            except requests.Timeout:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Timeout on attempt {attempt + 1} for {symbol} ({market_condition})")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All attempts timed out for {symbol} ({market_condition})")
                    return None
            except Exception as e:
                if attempt < self.retry_attempts - 1:
                    logger.warning(f"Attempt {attempt + 1} failed for {symbol} ({market_condition}): {str(e)}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"All attempts failed for {symbol} ({market_condition}): {str(e)}")
                    return None
    
    def save_historical_data(self, data: Dict[str, Any], symbol: str, market_condition: str, base_dir: Path) -> Optional[Path]:
        """Save historical data to JSON file."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{symbol}_{market_condition}_{timestamp}.json"
            filepath = base_dir / symbol / market_condition / filename
            
            # Create a temporary file first
            temp_filepath = filepath.with_suffix('.tmp')
            with open(temp_filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Verify the temporary file
            with open(temp_filepath, 'r') as f:
                loaded_data = json.load(f)
                if loaded_data != data:
                    raise Exception("Data corruption detected during save")
            
            # Rename temp file to final file
            temp_filepath.rename(filepath)
            
            logger.info(f"Saved data to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving data for {symbol} ({market_condition}): {str(e)}")
            # Clean up temp file if it exists
            if 'temp_filepath' in locals() and temp_filepath.exists():
                temp_filepath.unlink()
            return None
    
    def process_stock_condition(self, symbol: str, condition: str, base_dir: Path) -> Dict[str, Any]:
        """Process a single stock and market condition combination."""
        logger.info(f"\nProcessing {symbol} ({condition})...")
        
        data = self.fetch_historical_data(symbol, condition)
        if data:
            filepath = self.save_historical_data(data, symbol, condition, base_dir)
            if filepath:
                return {
                    'status': 'success',
                    'symbol': symbol,
                    'condition': condition,
                    'filepath': str(filepath),
                    'stats': data['validation_stats']
                }
            else:
                self.failed_files.append(base_dir / symbol / condition)
        
        return {
            'status': 'failed',
            'symbol': symbol,
            'condition': condition,
            'error': 'Failed to process data'
        }
    
    def collect_all_data(self) -> bool:
        """Collect historical data for all stocks and market conditions using parallel processing."""
        try:
            base_dir = self.create_data_directory()
            results = {
                'successful': [],
                'failed': []
            }
            
            # Calculate total tasks for progress bar
            total_tasks = len(STOCKS) * len(MARKET_PERIODS)
            
            # Process data in parallel
            with ThreadPoolExecutor(max_workers=DATA_COLLECTION_CONFIG['max_workers']) as executor:
                futures = []
                for symbol in STOCKS:
                    for condition in MARKET_PERIODS:
                        futures.append(
                            executor.submit(
                                self.process_stock_condition,
                                symbol,
                                condition,
                                base_dir
                            )
                        )
                
                # Use tqdm for progress tracking
                with tqdm(total=total_tasks, desc="Collecting data") as pbar:
                    for future in as_completed(futures):
                        result = future.result()
                        if result['status'] == 'success':
                            results['successful'].append(result)
                        else:
                            results['failed'].append(result)
                        pbar.update(1)
            
            # Clean up failed files
            self.cleanup_failed_files()
            
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
            
            # Return success status
            return len(results['failed']) == 0
            
        except Exception as e:
            logger.error(f"Error during data collection: {str(e)}")
            return False

if __name__ == '__main__':
    collector = DataCollector()
    success = collector.collect_all_data()
    exit(0 if success else 1) 