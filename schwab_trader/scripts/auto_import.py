import os
import sys
import logging
from datetime import datetime
import pandas as pd
from schwab_trader import create_app
from schwab_trader.models import db, Portfolio, Position

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_import_{}.log'.format(datetime.now().strftime('%Y%m%d'))),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('auto_import')

def parse_portfolio_file(file_path):
    """Parse the portfolio CSV file and return formatted data."""
    try:
        df = pd.read_csv(file_path)
        
        # Expected columns from Schwab positions page
        expected_columns = [
            'Symbol', 'Description', 'Quantity', 'Last Price', 
            'Average Cost', 'Market Value', 'Day Change $', 'Day Change %'
        ]
        
        # Validate required columns
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f'Missing required columns: {", ".join(missing_columns)}')
        
        # Clean and format the data
        portfolio_data = []
        for _, row in df.iterrows():
            position = {
                'symbol': row['Symbol'],
                'description': row['Description'],
                'quantity': float(row['Quantity']),
                'last_price': float(row['Last Price'].replace('$', '').replace(',', '')),
                'avg_cost': float(row['Average Cost'].replace('$', '').replace(',', '')),
                'market_value': float(row['Market Value'].replace('$', '').replace(',', '')),
                'day_change_dollar': float(row['Day Change $'].replace('$', '').replace(',', '')),
                'day_change_percent': float(row['Day Change %'].replace('%', ''))
            }
            portfolio_data.append(position)
        
        return portfolio_data
    except Exception as e:
        logger.error(f'Error parsing portfolio file: {str(e)}')
        raise

def import_portfolio(file_path):
    """Import portfolio data into the database."""
    try:
        app = create_app()
        with app.app_context():
            # Parse the portfolio file
            positions = parse_portfolio_file(file_path)
            
            # Calculate portfolio totals
            total_value = sum(pos['market_value'] for pos in positions)
            total_change = sum(pos['day_change_dollar'] for pos in positions)
            total_change_percent = (total_change / (total_value - total_change)) * 100 if total_value > 0 else 0
            
            # Create new portfolio record
            portfolio = Portfolio(
                total_value=total_value,
                total_change=total_change,
                total_change_percent=total_change_percent,
                date=datetime.now()
            )
            db.session.add(portfolio)
            db.session.flush()  # Get the portfolio ID
            
            # Create position records
            for pos in positions:
                position = Position(
                    portfolio_id=portfolio.id,
                    symbol=pos['symbol'],
                    description=pos['description'],
                    quantity=pos['quantity'],
                    last_price=pos['last_price'],
                    avg_cost=pos['avg_cost'],
                    market_value=pos['market_value'],
                    day_change_dollar=pos['day_change_dollar'],
                    day_change_percent=pos['day_change_percent']
                )
                db.session.add(position)
            
            db.session.commit()
            logger.info(f'Successfully imported portfolio with {len(positions)} positions')
            
    except Exception as e:
        logger.error(f'Error importing portfolio: {str(e)}')
        raise

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python auto_import.py <portfolio_file_path>')
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        logger.error(f'File not found: {file_path}')
        sys.exit(1)
    
    try:
        import_portfolio(file_path)
    except Exception as e:
        logger.error(f'Failed to import portfolio: {str(e)}')
        sys.exit(1) 