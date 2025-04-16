import os
import sys
import logging
from datetime import datetime
import pandas as pd
from flask import current_app

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schwab_trader import create_app
from schwab_trader.models import db, Portfolio, Position

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

def process_portfolio_data(csv_file='schwab_portfolio.csv'):
    """Process portfolio data from CSV file and save to database"""
    try:
        # Read CSV file
        logger.info(f"Reading portfolio data from {csv_file}")
        df = pd.read_csv(csv_file)
        
        # Clean up column names and data
        df.columns = [col.strip() for col in df.columns]
        
        # Create or get portfolio
        with db.session() as session:
            portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
            if not portfolio:
                portfolio = Portfolio(name='Schwab Portfolio')
                session.add(portfolio)
                session.commit()
            
            # Clear existing positions
            Position.query.filter_by(portfolio_id=portfolio.id).delete()
            
            # Add new positions
            for _, row in df.iterrows():
                try:
                    # Clean and convert numeric values
                    quantity = float(str(row['Quantity']).replace(',', ''))
                    price = float(str(row['Price']).replace('$', '').replace(',', ''))
                    market_value = float(str(row['Market Value']).replace('$', '').replace(',', ''))
                    day_change = float(str(row['Day Change $']).replace('$', '').replace(',', ''))
                    day_change_pct = float(str(row['Day Change %']).replace('%', ''))
                    cost_basis = float(str(row['Cost Basis']).replace('$', '').replace(',', ''))
                    
                    position = Position(
                        portfolio_id=portfolio.id,
                        symbol=row['Symbol'],
                        description=row['Description'],
                        quantity=quantity,
                        price=price,
                        market_value=market_value,
                        cost_basis=cost_basis,
                        day_change_dollar=day_change,
                        day_change_percent=day_change_pct,
                        security_type=row['Security Type']
                    )
                    session.add(position)
                except Exception as e:
                    logger.warning(f"Error processing row for {row['Symbol']}: {str(e)}")
                    continue
            
            session.commit()
            logger.info(f"Successfully imported {len(df)} positions")
            
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