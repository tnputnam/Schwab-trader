from schwab_trader import create_app, db
from schwab_trader.utils.alpha_vantage_api import AlphaVantageAPI
from schwab_trader.utils.schwab_api import SchwabAPI
import os

# Create the Flask application instance
app = create_app({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev'),
    'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY'),
    'SCHWAB_API_KEY': os.getenv('SCHWAB_API_KEY'),
    'SCHWAB_API_SECRET': os.getenv('SCHWAB_API_SECRET'),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///schwab_trader.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

# Initialize APIs within application context
with app.app_context():
    # Create database tables
    db.create_all()
    
    # Initialize APIs as Flask extensions
    alpha_vantage = AlphaVantageAPI()
    alpha_vantage.init_app(app)
    app.alpha_vantage = alpha_vantage
    
    schwab = SchwabAPI()
    schwab.init_app(app)
    app.schwab = schwab

if __name__ == '__main__':
    app.run(debug=True) 