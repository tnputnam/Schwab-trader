import os
import sys
from requests_oauthlib import OAuth2Session
import webbrowser
import logging
import json
from urllib.parse import urlparse, parse_qs, unquote
import base64
import requests
from flask import Flask, session, redirect, request, jsonify

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

# Updated with your ngrok URL
REDIRECT_URI = "https://edb0-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app/callback"

# Fixed URLs to use api.schwabapi.com
AUTHORIZATION_BASE_URL = "https://api.schwabapi.com/v1/oauth/authorize"  # Fixed domain
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"  # Fixed domain

# Updated scope to match Swagger UI
SCOPES = ["readonly"]  # Using only the readonly scope as shown in Swagger

@app.after_request
def after_request(response):
    response.headers.add('ngrok-skip-browser-warning', '1')
    return response

@app.route('/login')
def login():
    schwab = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )
    authorization_url, state = schwab.authorization_url(
        AUTHORIZATION_BASE_URL,
        response_type="code"  # Explicitly setting response_type
    )
    
    # Store state for later validation
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    try:
        schwab = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            state=session.get('oauth_state')
        )
        
        token = schwab.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        
        # Store token in session
        session['oauth_token'] = token
        
        # Test the token by getting account information
        accounts_response = schwab.get('https://api.schwabapi.com/v1/accounts')  # Fixed domain
        
        return jsonify({
            "success": True,
            "message": "Successfully authenticated with Schwab",
            "accounts": accounts_response.json()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

if __name__ == '__main__':
    # For development only
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print(f"Using Authorization URL: {AUTHORIZATION_BASE_URL}")
    print(f"Using Token URL: {TOKEN_URL}")
    print(f"Using Scopes: {SCOPES}")
    app.run(port=5001, debug=True)  # Changed port to 5001 