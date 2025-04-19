import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Any
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'logs/test_collection_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataCollectionTester:
    def __init__(self, num_runs: int = 5):
        self.num_runs = num_runs
        self.base_url = "http://localhost:5000/dashboard/api/test_data"
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Define test parameters
        self.stocks = ["TSLA", "NVDA", "AMZN", "AAPL"]
        self.market_conditions = ["bullish", "bearish", "neutral"]
        
        # Initialize results tracking
        self.all_results = []
        self.consistency_checks = {
            'price_ranges': {},
            'volume_stats': {},
            'trade_counts': {}
        }
    
    def run_test(self) -> Dict[str, Any]:
        """Run a single test iteration."""
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'successful': [],
            'failed': [],
            'stats': {}
        }
        
        for symbol in self.stocks:
            for condition in self.market_conditions:
                try:
                    # Fetch data
                    response = requests.get(f"{self.base_url}/{symbol}/{condition}")
                    if not response.ok:
                        raise Exception(f"API request failed: {response.status_code}")
                    
                    data = response.json()
                    if data['status'] != 'success':
                        raise Exception(f"API returned error: {data.get('message', 'Unknown error')}")
                    
                    # Validate data
                    validation_result = self.validate_data(data['data'], symbol, condition)
                    
                    if validation_result['is_valid']:
                        test_results['successful'].append({
                            'symbol': symbol,
                            'condition': condition,
                            'stats': validation_result['stats']
                        })
                    else:
                        test_results['failed'].append({
                            'symbol': symbol,
                            'condition': condition,
                            'error': validation_result['error']
                        })
                    
                except Exception as e:
                    test_results['failed'].append({
                        'symbol': symbol,
                        'condition': condition,
                        'error': str(e)
                    })
        
        return test_results
    
    def validate_data(self, data: Dict, symbol: str, condition: str) -> Dict:
        """Validate the data and return statistics."""
        try:
            # Check required fields
            required_fields = ['prices', 'trades', 'market_condition', 'symbol', 'period']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate prices data
            prices = data['prices']
            if len(prices) != 365:
                raise ValueError(f"Expected 365 days of data, got {len(prices)}")
            
            # Calculate statistics
            price_data = pd.DataFrame(prices)
            volume_data = pd.DataFrame(prices)['volume']
            
            stats = {
                'price_range': {
                    'min': price_data['low'].min(),
                    'max': price_data['high'].max(),
                    'avg': price_data['close'].mean(),
                    'std': price_data['close'].std()
                },
                'volume_stats': {
                    'total': volume_data.sum(),
                    'avg': volume_data.mean(),
                    'max': volume_data.max(),
                    'std': volume_data.std()
                },
                'trade_stats': {
                    'total': len(data['trades']),
                    'buy_count': sum(1 for t in data['trades'] if t['type'] == 'buy'),
                    'sell_count': sum(1 for t in data['trades'] if t['type'] == 'sell')
                }
            }
            
            return {
                'is_valid': True,
                'stats': stats
            }
            
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e)
            }
    
    def check_consistency(self, results: List[Dict]) -> Dict:
        """Check consistency across multiple test runs."""
        consistency_report = {
            'price_consistency': {},
            'volume_consistency': {},
            'trade_consistency': {}
        }
        
        for symbol in self.stocks:
            for condition in self.market_conditions:
                # Get all successful runs for this symbol/condition
                successful_runs = [
                    r for r in results 
                    if any(s['symbol'] == symbol and s['condition'] == condition for s in r['successful'])
                ]
                
                if not successful_runs:
                    continue
                
                # Calculate statistics across runs
                price_ranges = [
                    s['stats']['price_range']
                    for r in successful_runs
                    for s in r['successful']
                    if s['symbol'] == symbol and s['condition'] == condition
                ]
                
                volume_stats = [
                    s['stats']['volume_stats']
                    for r in successful_runs
                    for s in r['successful']
                    if s['symbol'] == symbol and s['condition'] == condition
                ]
                
                trade_stats = [
                    s['stats']['trade_stats']
                    for r in successful_runs
                    for s in r['successful']
                    if s['symbol'] == symbol and s['condition'] == condition
                ]
                
                # Calculate consistency metrics
                consistency_report['price_consistency'][f"{symbol}_{condition}"] = {
                    'min_range': min(r['min'] for r in price_ranges),
                    'max_range': max(r['max'] for r in price_ranges),
                    'avg_range': sum(r['avg'] for r in price_ranges) / len(price_ranges),
                    'std_range': np.std([r['max'] - r['min'] for r in price_ranges])
                }
                
                consistency_report['volume_consistency'][f"{symbol}_{condition}"] = {
                    'avg_volume': sum(s['avg'] for s in volume_stats) / len(volume_stats),
                    'std_volume': np.std([s['avg'] for s in volume_stats])
                }
                
                consistency_report['trade_consistency'][f"{symbol}_{condition}"] = {
                    'avg_trades': sum(s['total'] for s in trade_stats) / len(trade_stats),
                    'std_trades': np.std([s['total'] for s in trade_stats])
                }
        
        return consistency_report
    
    def run_all_tests(self):
        """Run multiple test iterations and analyze results."""
        logger.info(f"Starting {self.num_runs} test iterations")
        
        for i in range(self.num_runs):
            logger.info(f"\n{'='*50}")
            logger.info(f"Running test iteration {i+1}/{self.num_runs}")
            logger.info(f"{'='*50}")
            
            test_results = self.run_test()
            self.all_results.append(test_results)
            
            # Log summary for this iteration
            logger.info(f"\nTest iteration {i+1} summary:")
            logger.info(f"Successful: {len(test_results['successful'])}")
            logger.info(f"Failed: {len(test_results['failed'])}")
            
            # Save individual test results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = self.results_dir / f"test_results_{timestamp}.json"
            with open(result_file, 'w') as f:
                json.dump(test_results, f, indent=2)
            
            # Wait between runs
            time.sleep(2)
        
        # Analyze consistency
        consistency_report = self.check_consistency(self.all_results)
        
        # Save final report
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'total_runs': self.num_runs,
            'consistency_report': consistency_report,
            'all_results': self.all_results
        }
        
        report_file = self.results_dir / "final_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Log final summary
        logger.info("\nFinal Test Summary:")
        logger.info(f"Total runs: {self.num_runs}")
        logger.info(f"Consistency report saved to: {report_file}")
        
        # Log consistency metrics
        for symbol in self.stocks:
            for condition in self.market_conditions:
                key = f"{symbol}_{condition}"
                if key in consistency_report['price_consistency']:
                    logger.info(f"\n{symbol} ({condition}):")
                    logger.info(f"Price range consistency: {consistency_report['price_consistency'][key]['std_range']:.2f}")
                    logger.info(f"Volume consistency: {consistency_report['volume_consistency'][key]['std_volume']:.2f}")
                    logger.info(f"Trade count consistency: {consistency_report['trade_consistency'][key]['std_trades']:.2f}")

if __name__ == '__main__':
    tester = DataCollectionTester(num_runs=5)
    tester.run_all_tests() 