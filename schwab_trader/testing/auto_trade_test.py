import unittest
from datetime import datetime
import pandas as pd
import numpy as np
from flask import Flask, current_app
from schwab_trader import create_app, db
from schwab_trader.config import TestConfig
from schwab_trader.models.portfolio import Portfolio
from schwab_trader.models.position import Position
from schwab_trader.models.trade import Trade

class MockAlphaVantageAPI:
    def get_quote(self, symbol):
        mock_data = {
            'AAPL': {'price': 150.0, 'volume': 1000000},
            'MSFT': {'price': 300.0, 'volume': 800000}
        }
        return mock_data.get(symbol, {'price': 100.0, 'volume': 500000})

    def get_company_info(self, symbol):
        mock_data = {
            'AAPL': {'sector': 'Technology', 'industry': 'Consumer Electronics'},
            'MSFT': {'sector': 'Technology', 'industry': 'Software'}
        }
        return mock_data.get(symbol, {'sector': 'Unknown', 'industry': 'Unknown'})

class AutoTradeTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create database tables
        db.create_all()
        
        # Create test portfolio and positions
        self.portfolio = Portfolio(name='Test Portfolio')
        db.session.add(self.portfolio)
        
        positions = [
            Position(
                portfolio=self.portfolio,
                symbol='AAPL',
                quantity=10,
                price=145.0,
                cost_basis=140.0,
                market_value=1450.0
            ),
            Position(
                portfolio=self.portfolio,
                symbol='MSFT',
                quantity=5,
                price=290.0,
                cost_basis=280.0,
                market_value=1450.0
            )
        ]
        
        for position in positions:
            db.session.add(position)
        
        db.session.commit()
        
        self.mock_api = MockAlphaVantageAPI()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_portfolio_update(self):
        with self.app.app_context():
            positions = Position.query.all()
            for position in positions:
                quote = self.mock_api.get_quote(position.symbol)
                info = self.mock_api.get_company_info(position.symbol)
                
                position.price = quote['price']
                position.volume = quote['volume']
                position.sector = info['sector']
                position.industry = info['industry']
                position.market_value = position.quantity * position.price
                
                db.session.add(position)
            
            db.session.commit()
            
            # Verify updates
            aapl = Position.query.filter_by(symbol='AAPL').first()
            self.assertEqual(aapl.price, 150.0)
            self.assertEqual(aapl.sector, 'Technology')
            
            msft = Position.query.filter_by(symbol='MSFT').first()
            self.assertEqual(msft.price, 300.0)
            self.assertEqual(msft.sector, 'Technology')

    def test_trading_strategy(self):
        with self.app.app_context():
            positions = Position.query.all()
            for position in positions:
                quote = self.mock_api.get_quote(position.symbol)
                current_price = quote['price']
                
                if current_price > position.cost_basis * 1.1:  # 10% gain
                    trade = Trade(
                        portfolio=self.portfolio,
                        symbol=position.symbol,
                        quantity=-1,  # Sell 1 share
                        price=current_price,
                        timestamp=datetime.datetime.now()
                    )
                    db.session.add(trade)
                    position.quantity -= 1
                    position.market_value = position.quantity * current_price
                
                elif current_price < position.cost_basis * 0.9:  # 10% loss
                    trade = Trade(
                        portfolio=self.portfolio,
                        symbol=position.symbol,
                        quantity=1,  # Buy 1 share
                        price=current_price,
                        timestamp=datetime.datetime.now()
                    )
                    db.session.add(trade)
                    position.quantity += 1
                    position.market_value = position.quantity * current_price
                
                db.session.add(position)
            
            db.session.commit()
            
            # Verify trades
            trades = Trade.query.all()
            self.assertTrue(len(trades) > 0)

if __name__ == '__main__':
    unittest.main() 