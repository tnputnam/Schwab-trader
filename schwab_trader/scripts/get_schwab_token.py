import os
import requests
import webbrowser
from flask import Flask, request
import threading
import time
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Schwab API configuration
CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID')
CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI')
AUTH_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"
SCOPES = ["readonly", "trade"]

# Global variable to store the authorization code
auth_code = None

@app.route('/auth/callback')
def callback():
    """Handle the OAuth callback."""
    global auth_code
    auth_code = request.args.get('code')
    return "Authorization successful! You can close this window."

def run_flask():
    """Run the Flask server."""
    app.run(host='0.0.0.0', port=5000)

def get_authorization_code():
    """Get the authorization code from Schwab."""
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Wait for the server to start
    time.sleep(2)
    
    # Construct the authorization URL
    auth_params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES)
    }
    auth_url = f"{AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in auth_params.items())}"
    
    # Open the authorization URL in the default browser
    print(f"Opening authorization URL in browser: {auth_url}")
    webbrowser.open(auth_url)
    
    # Wait for the authorization code
    while not auth_code:
        time.sleep(1)
    
    return auth_code

def get_tokens(auth_code):
    """Get access token and refresh token using the authorization code."""
    try:
        # Make request to token endpoint
        response = requests.post(
            TOKEN_URL,
            data={
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': auth_code,
                'redirect_uri': REDIRECT_URI
            },
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        
        # Parse response
        token_data = response.json()
        
        # Save tokens to .env file
        with open('.env', 'a') as f:
            f.write(f"\n# Schwab API Tokens\n")
            f.write(f"SCHWAB_ACCESS_TOKEN={token_data['access_token']}\n")
            f.write(f"SCHWAB_REFRESH_TOKEN={token_data['refresh_token']}\n")
        
        print("\nTokens saved to .env file:")
        print(f"Access Token: {token_data['access_token'][:10]}...")
        print(f"Refresh Token: {token_data['refresh_token'][:10]}...")
        print("\nYou can now use these tokens for API access.")
        
    except Exception as e:
        print(f"Error getting tokens: {str(e)}")

if __name__ == '__main__':
    print("Starting Schwab OAuth flow...")
    print(f"Using redirect URI: {REDIRECT_URI}")
    
    # Get authorization code
    code = get_authorization_code()
    print(f"\nGot authorization code: {code[:10]}...")
    
    # Get tokens
    get_tokens(code) 