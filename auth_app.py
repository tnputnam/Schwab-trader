from flask import Flask, session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

# Updated with your ngrok URL
REDIRECT_URI = "https://edb0-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app/callback"

# Schwab OAuth endpoints
AUTHORIZATION_BASE_URL = "https://api.schwab.com/oauth2/authorize"
TOKEN_URL = "https://api.schwab.com/oauth2/token"

# Required scopes for your application
SCOPES = [
    "accounts_trading:read",
    "accounts_trading:write",
    "market_data:read"
]

@app.route('/login')
def login():
    schwab = OAuth2Session(
        CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES
    )
    authorization_url, state = schwab.authorization_url(AUTHORIZATION_BASE_URL)
    
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
        accounts_response = schwab.get('https://api.schwab.com/v1/accounts')
        
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
    app.run(port=5000)
