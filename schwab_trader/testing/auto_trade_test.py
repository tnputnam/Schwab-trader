import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from schwab_trader.models import Portfolio, Position
from schwab_trader.tasks.portfolio_updater import AlphaVantageAPI

class MockAlphaVantageAPI:
    """Mock API for testing auto-trading strategies"""
    def __init__(self):
        self.test_data = {
            'AAPL': {
                'price': 175.0,
                'volume': 1000000,
                'pe_ratio': 28.5,
                'market_cap': 2.8e12,
                'dividend_yield': 0.5,
                'eps': 6.15,
                'beta': 1.2
            },
            'MSFT': {
                'price': 330.0,
                'volume': 2000000,
                'pe_ratio': 32.0,
                'market_cap': 2.5e12,
                'dividend_yield': 0.7,
                'eps': 10.33,
                'beta': 0.9
            },
            'GOOGL': {
                'price': 150.0,
                'volume': 1500000,
                'pe_ratio': 25.0,
                'market_cap': 1.9e12,
                'dividend_yield': 0.0,
                'eps': 6.0,
                'beta': 1.1
            }
        }
    
    def get_quote(self, symbol):
        """Get mock quote data"""
        if symbol in self.test_data:
            return {
                '05. price': str(self.test_data[symbol]['price']),
                '06. volume': str(self.test_data[symbol]['volume']),
                '09. change': str(np.random.uniform(-5, 5)),
                '10. change percent': str(np.random.uniform(-2, 2)) + '%'
            }
        return None
    
    def get_company_info(self, symbol):
        """Get mock company info"""
        if symbol in self.test_data:
            return {
                'Sector': 'Technology',
                'Industry': 'Software',
                'PERatio': str(self.test_data[symbol]['pe_ratio']),
                'MarketCapitalization': str(self.test_data[symbol]['market_cap']),
                'DividendYield': str(self.test_data[symbol]['dividend_yield']),
                'EPS': str(self.test_data[symbol]['eps']),
                'Beta': str(self.test_data[symbol]['beta'])
            }
        return None

class TestAutoTrading(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.api = MockAlphaVantageAPI()
        self.test_portfolio = Portfolio(
            name='Test Portfolio',
            total_value=100000.0,
            cash_value=20000.0,
            total_gain=0.0,
            total_gain_percent=0.0,
            day_change=0.0,
            day_change_percent=0.0
        )
        
        # Add test positions
        self.positions = [
            Position(
                symbol='AAPL',
                quantity=100,
                price=175.0,
                cost_basis=170.0,
                market_value=17500.0,
                day_change_dollar=0.0,
                day_change_percent=0.0,
                sector='Technology',
                industry='Consumer Electronics'
            ),
            Position(
                symbol='MSFT',
                quantity=50,
                price=330.0,
                cost_basis=320.0,
                market_value=16500.0,
                day_change_dollar=0.0,
                day_change_percent=0.0,
                sector='Technology',
                industry='Software'
            )
        ]
    
    def test_portfolio_update(self):
        """Test portfolio update with mock data"""
        for position in self.positions:
            quote = self.api.get_quote(position.symbol)
            company_info = self.api.get_company_info(position.symbol)
            
            self.assertIsNotNone(quote)
            self.assertIsNotNone(company_info)
            
            # Update position data
            position.price = float(quote['05. price'])
            position.market_value = position.quantity * position.price
            position.day_change_dollar = float(quote['09. change'])
            position.day_change_percent = float(quote['10. change percent'].replace('%', ''))
            
            # Update additional metrics
            position.sector = company_info.get('Sector', position.sector)
            position.industry = company_info.get('Industry', position.industry)
            position.pe_ratio = float(company_info.get('PERatio', 0))
            position.market_cap = float(company_info.get('MarketCapitalization', 0))
            position.dividend_yield = float(company_info.get('DividendYield', 0))
            position.eps = float(company_info.get('EPS', 0))
            position.beta = float(company_info.get('Beta', 0))
            position.volume = float(quote.get('06. volume', 0))
    
    def test_trading_strategy(self):
        """Test basic trading strategy"""
        # Example strategy: Buy if price drops more than 2%, sell if it rises more than 2%
        for position in self.positions:
            current_price = position.price
            cost_basis = position.cost_basis
            price_change_percent = ((current_price - cost_basis) / cost_basis) * 100
            
            if price_change_percent < -2.0:
                # Buy signal
                print(f"Buy signal for {position.symbol}: Price dropped {price_change_percent:.2f}%")
            elif price_change_percent > 2.0:
                # Sell signal
                print(f"Sell signal for {position.symbol}: Price rose {price_change_percent:.2f}%")
            else:
                # Hold
                print(f"Hold {position.symbol}: Price change {price_change_percent:.2f}%")

if __name__ == '__main__':
    unittest.main() 