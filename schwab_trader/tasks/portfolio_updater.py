import os
import time
import logging
from datetime import datetime
import pandas as pd
import requests
from flask import current_app
from collections import defaultdict
from threading import Thread

# Configure logging
logger = logging.getLogger('portfolio_updater')
handler = logging.FileHandler('logs/portfolio_updater_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AlphaVantageAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = 'https://www.alphavantage.co/query'
        
    def get_quote(self, symbol):
        """Get real-time quote for a symbol."""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        data = response.json()
        if 'Global Quote' in data:
            return data['Global Quote']
        return None
        
    def get_company_info(self, symbol):
        """Get company overview including sector and additional metrics."""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json()
        
    def get_income_statement(self, symbol):
        """Get income statement data for key metrics."""
        params = {
            'function': 'INCOME_STATEMENT',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

def update_portfolio_data():
    """Update portfolio data using Alpha Vantage API."""
    try:
        # Initialize Alpha Vantage API
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        api = AlphaVantageAPI(api_key)
        
        with current_app.app_context():
            from schwab_trader.models import db, Portfolio, Position, Sector
            
            portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
            if not portfolio:
                logger.error("Portfolio not found")
                return
                
            positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
            if not positions:
                logger.error("No positions found")
                return
                
            # Update each position
            sector_totals = defaultdict(float)
            total_value = 0
            total_cost = 0
            total_day_change = 0
            
            for position in positions:
                try:
                    # Get real-time quote
                    quote = api.get_quote(position.symbol)
                    if not quote:
                        logger.warning(f"Could not get quote for {position.symbol}")
                        continue
                        
                    # Get company info for additional metrics
                    company_info = api.get_company_info(position.symbol)
                    
                    # Update position data
                    position.price = float(quote['05. price'])
                    position.market_value = position.quantity * position.price
                    position.day_change_dollar = float(quote['09. change'])
                    position.day_change_percent = float(quote['10. change percent'].replace('%', ''))
                    
                    # Add additional metrics if available
                    if company_info:
                        position.sector = company_info.get('Sector', position.sector)
                        position.industry = company_info.get('Industry', position.industry)
                        position.pe_ratio = float(company_info.get('PERatio', 0))
                        position.market_cap = float(company_info.get('MarketCapitalization', 0))
                        position.dividend_yield = float(company_info.get('DividendYield', 0))
                        position.eps = float(company_info.get('EPS', 0))
                        position.beta = float(company_info.get('Beta', 0))
                        position.volume = float(quote.get('06. volume', 0))
                    
                    # Update totals
                    sector_totals[position.sector] += position.market_value
                    total_value += position.market_value
                    total_cost += position.cost_basis
                    total_day_change += position.day_change_dollar
                    
                except Exception as e:
                    logger.warning(f"Error updating position {position.symbol}: {str(e)}")
                    continue
            
            # Update sector records
            Sector.query.filter_by(portfolio_id=portfolio.id).delete()
            for sector_name, sector_value in sector_totals.items():
                sector = Sector(
                    portfolio_id=portfolio.id,
                    name=sector_name,
                    market_value=sector_value,
                    percentage=(sector_value / total_value * 100) if total_value > 0 else 0
                )
                db.session.add(sector)
            
            # Update portfolio summary
            portfolio.total_value = total_value
            portfolio.total_gain = total_value - total_cost
            portfolio.total_gain_percent = (portfolio.total_gain / total_cost * 100) if total_cost > 0 else 0
            portfolio.day_change = total_day_change
            portfolio.day_change_percent = (total_day_change / (total_value - total_day_change) * 100) if total_value > total_day_change else 0
            
            db.session.commit()
            logger.info(f"Successfully updated portfolio with {len(positions)} positions")
            
    except Exception as e:
        logger.error(f"Error updating portfolio data: {str(e)}")

def start_portfolio_updater(interval_minutes=5):
    """Start the portfolio updater in a background thread."""
    def updater_loop():
        while True:
            try:
                update_portfolio_data()
            except Exception as e:
                logger.error(f"Error in updater loop: {str(e)}")
            time.sleep(interval_minutes * 60)
    
    thread = Thread(target=updater_loop, daemon=True)
    thread.start()
    logger.info(f"Portfolio updater started with {interval_minutes} minute interval")
    return thread 