from schwab_trader import create_app
from schwab_trader.utils.alpha_vantage_api import AlphaVantageAPI
from schwab_trader.utils.schwab_api import SchwabAPI
import os

app = create_app({
    'SECRET_KEY': os.getenv('SECRET_KEY', 'dev'),
    'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY'),
    'SCHWAB_API_KEY': os.getenv('SCHWAB_API_KEY'),
    'SCHWAB_API_SECRET': os.getenv('SCHWAB_API_SECRET'),
    'SQLALCHEMY_DATABASE_URI': 'sqlite:///schwab_trader.db',
    'SQLALCHEMY_TRACK_MODIFICATIONS': False
})

# Initialize APIs with app context
with app.app_context():
    alpha_vantage = AlphaVantageAPI(app)
    schwab = SchwabAPI(app)

if __name__ == '__main__':
    app.run(debug=True) 