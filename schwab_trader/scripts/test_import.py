import os
import sys
import logging
from datetime import datetime
import pandas as pd

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schwab_trader import create_app, db
from schwab_trader.models import Portfolio, Position

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/test_import_{}.log'.format(datetime.now().strftime('%Y%m%d'))),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('test_import')

def create_test_data():
    """Create a test portfolio CSV file."""
    test_data = {
        'Symbol': ['AAPL', 'MSFT', 'GOOGL'],
        'Description': ['Apple Inc', 'Microsoft Corp', 'Alphabet Inc Class A'],
        'Quantity': [10, 5, 3],
        'Last Price': ['$150.25', '$300.50', '$2800.75'],
        'Average Cost': ['$145.00', '$295.00', '$2750.00'],
        'Market Value': ['$1,502.50', '$1,502.50', '$8,402.25'],
        'Day Change $': ['$5.25', '$5.50', '$50.75'],
        'Day Change %': ['3.5%', '1.8%', '1.8%']
    }
    
    df = pd.DataFrame(test_data)
    test_file = 'test_portfolio.csv'
    df.to_csv(test_file, index=False)
    return test_file

def test_import():
    """Test the portfolio import functionality."""
    try:
        # Create test data
        test_file = create_test_data()
        logger.info(f"Created test file: {test_file}")
        
        # Initialize Flask app
        app = create_app()
        with app.app_context():
            # Create database tables
            db.create_all()
            logger.info("Created database tables")
            
            # Import test data
            from auto_import import import_portfolio
            import_portfolio(test_file)
            logger.info("Successfully imported test data")
            
            # Verify data was imported
            portfolio = Portfolio.query.first()
            if portfolio:
                logger.info(f"Found portfolio with total value: ${portfolio.total_value:,.2f}")
                positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
                logger.info(f"Found {len(positions)} positions")
                for pos in positions:
                    logger.info(f"Position: {pos.symbol} - {pos.quantity} shares @ ${pos.last_price}")
            else:
                logger.error("No portfolio data found in database")
            
            # Clean up
            os.remove(test_file)
            logger.info("Cleaned up test file")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == '__main__':
    test_import() 