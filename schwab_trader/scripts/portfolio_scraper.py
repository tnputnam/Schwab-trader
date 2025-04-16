import os
import sys
import logging
from datetime import datetime
import pandas as pd
import requests
from flask import current_app
from collections import defaultdict

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schwab_trader import create_app
from schwab_trader.models import db, Portfolio, Position, Sector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/portfolio_scraper_{}.log'.format(datetime.now().strftime('%Y%m%d'))),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('portfolio_scraper')

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
        """Get company overview including sector."""
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

def process_portfolio_data(csv_file='schwab_portfolio.csv'):
    """Process portfolio data from CSV file and save to database"""
    try:
        # Read CSV file, skipping the first two rows
        logger.info(f"Reading portfolio data from {csv_file}")
        df = pd.read_csv(csv_file, skiprows=2)
        
        # Clean up column names and data
        df.columns = [col.strip() for col in df.columns]
        
        # Map column names to match our expected format
        column_mapping = {
            'Symbol': 'Symbol',
            'Description': 'Description',
            'Qty (Quantity)': 'Quantity',
            'Price': 'Price',
            'Mkt Val (Market Value)': 'Market Value',
            'Day Chng $ (Day Change $)': 'Day Change $',
            'Day Chng % (Day Change %)': 'Day Change %',
            'Cost Basis': 'Cost Basis',
            'Security Type': 'Security Type'
        }
        df = df.rename(columns=column_mapping)
        
        # Initialize Alpha Vantage API
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        api = AlphaVantageAPI(api_key)
        
        # Create or get portfolio
        with db.session() as session:
            portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
            if not portfolio:
                portfolio = Portfolio(name='Schwab Portfolio')
                session.add(portfolio)
                session.commit()
            
            # Clear existing positions and sectors
            Position.query.filter_by(portfolio_id=portfolio.id).delete()
            Sector.query.filter_by(portfolio_id=portfolio.id).delete()
            
            # Process regular positions
            positions_data = []
            sector_totals = defaultdict(float)
            total_value = 0
            total_cost = 0
            total_day_change = 0
            
            for _, row in df.iterrows():
                try:
                    if row['Symbol'] in ['Cash & Cash Investments', 'Account Total']:
                        continue
                        
                    symbol = row['Symbol']
                    
                    # Get real-time quote
                    quote = api.get_quote(symbol)
                    if not quote:
                        logger.warning(f"Could not get quote for {symbol}")
                        continue
                        
                    # Get company info for sector
                    company_info = api.get_company_info(symbol)
                    sector = company_info.get('Sector', 'Other')
                    
                    # Clean and convert numeric values
                    quantity = float(str(row['Quantity']).replace(',', ''))
                    price = float(quote['05. price'])
                    market_value = quantity * price
                    day_change = float(quote['09. change'])
                    day_change_pct = float(quote['10. change percent'].replace('%', ''))
                    cost_basis = float(str(row['Cost Basis']).replace('$', '').replace(',', ''))
                    
                    position = Position(
                        portfolio_id=portfolio.id,
                        symbol=symbol,
                        description=row['Description'],
                        quantity=quantity,
                        price=price,
                        market_value=market_value,
                        cost_basis=cost_basis,
                        day_change_dollar=day_change,
                        day_change_percent=day_change_pct,
                        security_type=row['Security Type'],
                        sector=sector
                    )
                    session.add(position)
                    positions_data.append(position)
                    
                    # Update totals
                    sector_totals[sector] += market_value
                    total_value += market_value
                    total_cost += cost_basis
                    total_day_change += day_change
                    
                except Exception as e:
                    logger.warning(f"Error processing row for {row['Symbol']}: {str(e)}")
                    continue
            
            # Create sector records
            for sector_name, sector_value in sector_totals.items():
                sector = Sector(
                    portfolio_id=portfolio.id,
                    name=sector_name,
                    market_value=sector_value,
                    percentage=(sector_value / total_value * 100) if total_value > 0 else 0
                )
                session.add(sector)
            
            # Update portfolio summary
            portfolio.total_value = total_value
            portfolio.total_gain = total_value - total_cost
            portfolio.total_gain_percent = (portfolio.total_gain / total_cost * 100) if total_cost > 0 else 0
            portfolio.day_change = total_day_change
            portfolio.day_change_percent = (total_day_change / (total_value - total_day_change) * 100) if total_value > total_day_change else 0
            
            # Find cash position
            try:
                cash_row = df[df['Symbol'] == 'Cash & Cash Investments'].iloc[0]
                portfolio.cash_value = float(str(cash_row['Market Value']).replace('$', '').replace(',', ''))
            except:
                portfolio.cash_value = 0
                logger.warning("Could not find cash position")
            
            session.commit()
            logger.info(f"Successfully imported {len(positions_data)} positions")
            
    except Exception as e:
        logger.error(f"Error processing portfolio data: {str(e)}")
        raise

def main():
    try:
        app = create_app()
        with app.app_context():
            process_portfolio_data()
            logger.info("Portfolio data import completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to import portfolio: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 