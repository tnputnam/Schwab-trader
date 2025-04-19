"""Mock authentication module for testing."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_schwab_token():
    """Get mock Schwab API token for testing."""
    return os.getenv('SCHWAB_API_KEY', 'test_schwab_token') 