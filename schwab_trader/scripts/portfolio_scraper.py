import os
import sys
import logging
import json
from datetime import datetime
import requests
from urllib.parse import urljoin
import pandas as pd
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

class SchwabAPI:
    """Interface with Schwab OpenAPI"""
    
    BASE_URL = "https://api.schwab.com/v1"  # Base URL for Schwab's API
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        
    def authenticate(self):
        """Authenticate with Schwab API using OAuth2"""
        try:
            auth_url = urljoin(self.BASE_URL, "/oauth2/token")
            response = requests.post(
                auth_url,
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"}
            )
            response.raise_for_status()
            self.access_token = response.json()["access_token"]
            logger.info("Successfully authenticated with Schwab API")
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            raise
    
    def get_positions(self):
        """Fetch portfolio positions from Schwab API"""
        if not self.access_token:
            self.authenticate()
            
        try:
            positions_url = urljoin(self.BASE_URL, "/accounts/positions")
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            response = requests.get(positions_url, headers=headers)
            response.raise_for_status()
            
            positions_data = response.json()
            logger.info(f"Successfully retrieved {len(positions_data)} positions")
            return positions_data
            
        except Exception as e:
            logger.error(f"Failed to fetch positions: {str(e)}")
            raise

def save_portfolio_data(positions, filename='schwab_portfolio.csv'):
    """Save portfolio data to CSV and database"""
    try:
        # Convert positions to DataFrame
        df = pd.DataFrame(positions)
        
        # Save to CSV
        df.to_csv(filename, index=False)
        logger.info(f"Portfolio data saved to {filename}")
        
        # Update database
        with db.session() as session:
            # Clear existing positions
            session.query(Position).delete()
            
            # Add new positions
            for pos in positions:
                position = Position(
                    symbol=pos['symbol'],
                    description=pos['description'],
                    quantity=pos['quantity'],
                    price=pos['price'],
                    market_value=pos['marketValue'],
                    cost_basis=pos['costBasis'],
                    day_change_dollar=pos['dayChange'],
                    day_change_percent=pos['dayChangePercent'],
                    security_type=pos['securityType']
                )
                session.add(position)
            
            session.commit()
            logger.info("Database updated with new positions")
            
        return filename
    except Exception as e:
        logger.error(f"Error saving portfolio data: {str(e)}")
        raise

def main():
    try:
        # Load API credentials from environment variables
        client_id = os.getenv('SCHWAB_CLIENT_ID')
        client_secret = os.getenv('SCHWAB_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("Missing Schwab API credentials. Please set SCHWAB_CLIENT_ID and SCHWAB_CLIENT_SECRET environment variables.")
        
        # Initialize Schwab API client
        schwab = SchwabAPI(client_id, client_secret)
        
        # Fetch portfolio data
        positions = schwab.get_positions()
        
        # Save data
        filename = save_portfolio_data(positions)
        logger.info(f"Successfully retrieved and saved portfolio data to {filename}")
            
    except Exception as e:
        logger.error(f"Failed to retrieve portfolio: {str(e)}")
        raise

if __name__ == "__main__":
    main() 