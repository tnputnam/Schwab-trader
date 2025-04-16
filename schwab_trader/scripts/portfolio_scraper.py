import os
import sys
import logging
import time
from datetime import datetime

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
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

def setup_driver():
    """Set up the Chrome WebDriver with appropriate options."""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')
    return webdriver.Chrome(options=options)

def wait_for_element(driver, by, value, timeout=10):
    """Wait for an element to be present and visible."""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        logger.error(f"Timeout waiting for element: {value}")
        return None

def download_portfolio_data():
    """Download portfolio data from Schwab's website."""
    driver = None
    try:
        driver = setup_driver()
        driver.get("https://client.schwab.com/Login/SignOn/CustomerCenterLogin.aspx")
        
        logger.info("Waiting for manual login...")
        # Wait for user to log in manually
        wait_for_element(driver, By.ID, "positions", timeout=300)  # 5 minute timeout for login
        
        logger.info("Login detected, navigating to positions page...")
        # Navigate to positions page
        positions_link = wait_for_element(driver, By.LINK_TEXT, "Positions")
        positions_link.click()
        
        # Wait for positions table to load
        logger.info("Waiting for positions table to load...")
        table = wait_for_element(driver, By.CLASS_NAME, "positions-table")
        
        if not table:
            raise Exception("Could not find positions table")
        
        # Extract data from the table
        logger.info("Extracting portfolio data...")
        rows = table.find_elements(By.TAG_NAME, "tr")
        
        # Prepare data for DataFrame
        data = []
        headers = ['Symbol', 'Description', 'Quantity', 'Last Price', 
                  'Average Cost', 'Market Value', 'Day Change $', 'Day Change %']
        
        for row in rows[1:]:  # Skip header row
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= len(headers):
                row_data = {headers[i]: cells[i].text for i in range(len(headers))}
                data.append(row_data)
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Save to CSV
        backup_dir = "/home/thomas/schwab_trader_backups/portfolio"
        os.makedirs(backup_dir, exist_ok=True)
        filename = f"{backup_dir}/portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        logger.info(f"Portfolio data saved to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error during portfolio data retrieval: {str(e)}")
        raise
    finally:
        if driver:
            driver.quit()

if __name__ == '__main__':
    try:
        csv_file = download_portfolio_data()
        if csv_file:
            # Import the portfolio data
            from auto_import import import_portfolio
            import_portfolio(csv_file)
    except Exception as e:
        logger.error(f"Failed to retrieve and import portfolio: {str(e)}")
        sys.exit(1) 