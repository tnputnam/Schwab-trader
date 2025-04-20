import os
from schwab_trader import create_app, db
from schwab_trader.utils.alpha_vantage_api import AlphaVantageAPI
from schwab_trader.utils.schwab_api import SchwabAPI
from schwab_trader.utils.logger import setup_logger

# Set up logging
logger = setup_logger(__name__)

def create_and_configure_app():
    """Create and configure the Flask application."""
    app = create_app({
        'SECRET_KEY': os.getenv('SECRET_KEY', 'dev'),
        'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY'),
        'SCHWAB_API_KEY': os.getenv('SCHWAB_API_KEY'),
        'SCHWAB_API_SECRET': os.getenv('SCHWAB_API_SECRET'),
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///schwab_trader.db',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False
    })
    
    with app.app_context():
        try:
            # Create database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Initialize APIs as Flask extensions
            alpha_vantage = AlphaVantageAPI()
            alpha_vantage.init_app(app)
            app.alpha_vantage = alpha_vantage
            logger.info("AlphaVantage API initialized successfully")
            
            schwab = SchwabAPI()
            schwab.init_app(app)
            app.schwab = schwab
            logger.info("Schwab API initialized successfully")
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.error(f"Error during initialization: {str(e)}")
            raise
    
    return app

# Create the Flask application instance
app = create_and_configure_app()

if __name__ == '__main__':
    app.run(debug=True) 