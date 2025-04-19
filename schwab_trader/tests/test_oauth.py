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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key_123')  # Required for session management

# Get credentials from environment variables
CLIENT_ID = os.getenv('SCHWAB_CLIENT_ID')
CLIENT_SECRET = os.getenv('SCHWAB_CLIENT_SECRET')
REDIRECT_URI = os.getenv('SCHWAB_REDIRECT_URI')

# Fixed URLs to use api.schwabapi.com
AUTHORIZATION_BASE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# Updated scope to match Swagger UI
SCOPES = ["readonly"]  # Using only the readonly scope as shown in Swagger

@app.after_request
def after_request(response):
    response.headers.add('ngrok-skip-browser-warning', '1')
    return response

@app.route('/')
def index():
    print("Index route accessed!")  # Debug print
    return """
    <h1>Schwab OAuth Test</h1>
    <p>Authorization URL: {}</p>
    <p>Token URL: {}</p>
    <p>Scopes: {}</p>
    <a href="/login">Login with Schwab</a>
    """.format(AUTHORIZATION_BASE_URL, TOKEN_URL, SCOPES)

@app.route('/login')
def login():
    print("Login route accessed!")  # Debug print
    schwab = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )
    authorization_url, state = schwab.authorization_url(
        AUTHORIZATION_BASE_URL,
        response_type="code"  # Explicitly setting response_type
    )
    
    print(f"Generated Authorization URL: {authorization_url}")  # Debug print
    
    # Store state for later validation
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    logger.info("Callback route accessed")
    try:
        if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
            raise ValueError("Missing required environment variables")
            
        schwab = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            state=session.get('oauth_state')
        )
        
        logger.info(f"Callback URL: {request.url}")
        
        token = schwab.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        
        # Store token in session
        session['oauth_token'] = token
        
        # Test the token by getting account information
        accounts_response = schwab.get('https://api.schwabapi.com/v1/accounts')
        
        return jsonify({
            "success": True,
            "message": "Successfully authenticated with Schwab",
            "accounts": accounts_response.json()
        })
        
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

if __name__ == '__main__':
    # For development only
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    print("Starting Flask app...")  # Debug print
    print(f"Using Authorization URL: {AUTHORIZATION_BASE_URL}")
    print(f"Using Token URL: {TOKEN_URL}")
    print(f"Using Scopes: {SCOPES}")
    app.run(host='0.0.0.0', port=5000, debug=True)  # Changed port to 5000 