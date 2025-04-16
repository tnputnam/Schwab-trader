import os
import sys
import logging
import time
from datetime import datetime

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
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
    """Set up Chrome WebDriver with appropriate options."""
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--user-data-dir=./chrome_profile')
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_login(driver, timeout=300):
    """Wait for user to log in manually."""
    print("\nPlease log in to Schwab in the browser window that just opened.")
    print("The script will wait for you to complete the login process.")
    print("You have 5 minutes to log in.")
    print("After logging in, the script will automatically proceed with data extraction.\n")
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_url = driver.current_url
        if 'positions' in current_url.lower():
            logger.info("Login detected, proceeding with data extraction...")
            return True
        time.sleep(5)
    
    raise TimeoutException("Login timeout - please try again")

def extract_portfolio_data(driver):
    """Extract portfolio data from Schwab positions page."""
    try:
        # Wait for any table that might contain position data
        logger.info("Waiting for positions data to load...")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
        
        # Find all tables on the page
        tables = driver.find_elements(By.TAG_NAME, "table")
        logger.info(f"Found {len(tables)} tables on the page")
        
        # Look for the table containing position data
        positions_table = None
        for table in tables:
            try:
                # Check if table has expected columns
                headers = table.find_elements(By.TAG_NAME, "th")
                header_texts = [h.text.lower() for h in headers]
                if 'symbol' in header_texts:  # Schwab positions table always has a Symbol column
                    positions_table = table
                    break
            except:
                continue
        
        if not positions_table:
            raise NoSuchElementException("Could not find positions table with Symbol column")
        
        # Extract data from the table
        rows = positions_table.find_elements(By.TAG_NAME, "tr")
        data = []
        
        for row in rows[1:]:  # Skip header row
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 12:  # Schwab positions table has at least 12 columns
                    # Clean and convert numeric values
                    quantity = cells[2].text.strip().replace(',', '')
                    price = cells[3].text.strip().replace('$', '').replace(',', '')
                    mkt_value = cells[5].text.strip().replace('$', '').replace(',', '')
                    day_change_dollar = cells[6].text.strip().replace('$', '').replace(',', '')
                    day_change_percent = cells[7].text.strip().replace('%', '')
                    cost_basis = cells[8].text.strip().replace('$', '').replace(',', '')
                    
                    position = {
                        'Symbol': cells[0].text.strip(),
                        'Description': cells[1].text.strip(),
                        'Quantity': float(quantity) if quantity else 0.0,
                        'Price': float(price) if price else 0.0,
                        'Price Change $': cells[4].text.strip(),
                        'Market Value': float(mkt_value) if mkt_value else 0.0,
                        'Day Change $': float(day_change_dollar) if day_change_dollar else 0.0,
                        'Day Change %': float(day_change_percent) if day_change_percent else 0.0,
                        'Cost Basis': float(cost_basis) if cost_basis else 0.0,
                        'Gain $ (Gain/Loss $)': cells[9].text.strip(),
                        'Gain % (Gain/Loss %)': cells[10].text.strip(),
                        'Security Type': cells[11].text.strip()
                    }
                    data.append(position)
            except Exception as e:
                logger.warning(f"Error processing row: {e}")
                continue
        
        if not data:
            raise Exception("No position data found in table")
        
        return pd.DataFrame(data)
        
    except Exception as e:
        logger.error(f"Error during portfolio data extraction: {str(e)}")
        raise

def save_portfolio_data(df, filename='schwab_portfolio.csv'):
    """Save portfolio data to CSV file."""
    try:
        df.to_csv(filename, index=False)
        logger.info(f"Portfolio data saved to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error saving portfolio data: {str(e)}")
        raise

def main():
    driver = None
    try:
        driver = setup_driver()
        driver.get("https://client.schwab.com/")
        
        # Wait for manual login
        if wait_for_login(driver):
            # Extract portfolio data
            portfolio_df = extract_portfolio_data(driver)
            
            # Save to CSV
            filename = save_portfolio_data(portfolio_df)
            logger.info(f"Successfully extracted and saved portfolio data to {filename}")
            
    except Exception as e:
        logger.error(f"Failed to retrieve portfolio: {str(e)}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main() 