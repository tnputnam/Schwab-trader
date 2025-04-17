from flask import Flask, session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

import os
import sys

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from schwab_trader.utils.schwab_oauth import SchwabOAuth
import webbrowser

def test_oauth_flow():
    # Initialize OAuth client
    schwab = SchwabOAuth()
    
    # Get authorization URL
    auth_url, state = schwab.get_authorization_url()
    
    print("\nSchwab OAuth Test")
    print("================")
    print(f"\n1. Opening authorization URL in your browser...")
    print(f"URL: {auth_url}")
    
    # Open the URL in browser
    webbrowser.open(auth_url)
    
    # Wait for user to authorize and get the callback URL
    print("\n2. After authorizing, copy the full callback URL from your browser")
    callback_url = input("Enter the callback URL: ")
    
    # Exchange authorization code for token
    token = schwab.fetch_token(callback_url)
    
    if token:
        print("\n3. Successfully obtained token!")
        print("\n4. Testing API access by getting accounts...")
        accounts = schwab.get_accounts(token)
        if accounts:
            print("Successfully retrieved accounts!")
            print(f"Accounts: {accounts}")
        else:
            print("Error getting accounts")
    else:
        print("Error obtaining token")

if __name__ == "__main__":
    test_oauth_flow() 