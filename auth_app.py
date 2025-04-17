from flask import Flask, session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

# Updated with your ngrok URL
REDIRECT_URI = "https://fff5-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app/callback"

# Fixed URLs to use api.schwabapi.com
AUTHORIZATION_BASE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# Updated scope to match Swagger UI
SCOPES = ["readonly"]  # Using only the readonly scope as shown in Swagger

@app.route('/')
def index():
    return """
    <h1>Schwab OAuth Test</h1>
    <p>Authorization URL: {}</p>
    <p>Token URL: {}</p>
    <p>Scopes: {}</p>
    <a href="/login">Login with Schwab</a>
    """.format(AUTHORIZATION_BASE_URL, TOKEN_URL, SCOPES)

@app.route('/login')
def login():
    logger.debug("Starting login process")
    schwab = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )
    authorization_url, state = schwab.authorization_url(
        AUTHORIZATION_BASE_URL,
        response_type="code"  # Explicitly setting response_type
    )
    
    logger.debug(f"Generated Authorization URL: {authorization_url}")
    
    # Store state for later validation
    session['oauth_state'] = state
    return redirect(authorization_url)

@app.route('/callback')
def callback():
    logger.debug("Received callback")
    try:
        schwab = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            state=session.get('oauth_state')
        )
        
        logger.debug(f"Callback URL: {request.url}")
        
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
    logger.info("Starting Flask app...")
    logger.info(f"Using Authorization URL: {AUTHORIZATION_BASE_URL}")
    logger.info(f"Using Token URL: {TOKEN_URL}")
    logger.info(f"Using Scopes: {SCOPES}")
    app.run(host='0.0.0.0', port=5000, debug=True)
