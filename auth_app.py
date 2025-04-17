from flask import Flask, session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import os
import logging
import jwt

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

# Updated scope to match Schwab's API
SCOPES = ["api"]  # Using the api scope as returned by the token endpoint

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
    authorization_url, state = schwab.authorization_url(AUTHORIZATION_BASE_URL)
    
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
        
        token_response = schwab.fetch_token(
            TOKEN_URL,
            client_secret=CLIENT_SECRET,
            authorization_response=request.url
        )
        
        # Store token in session
        session['oauth_token'] = token_response
        
        # Get the Schwab-Client-Correlid from the token response headers
        client_correlid = request.headers.get('Schwab-Client-Correlid')
        if not client_correlid:
            # Extract from token response headers if available
            client_correlid = token_response.get('jti', '')
            if not client_correlid:
                # Use the jti from the id_token as fallback
                try:
                    id_token = jwt.decode(token_response['id_token'], options={"verify_signature": False})
                    client_correlid = id_token.get('jti', '')
                except Exception as e:
                    logger.warning(f"Could not decode id_token: {e}")
        
        logger.debug(f"Using client correlation ID: {client_correlid}")
        
        # Common headers for all requests
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {token_response["access_token"]}',
            'X-Authorization': f'Bearer {token_response["access_token"]}',
            'Schwab-Client-Correlid': client_correlid,
            'Origin': REDIRECT_URI.split('/callback')[0],
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try different API endpoints
        api_endpoints = [
            'v1/accounts',  # Try base accounts endpoint
            'v1/trading/accounts',  # Try trading accounts endpoint
            'v1/brokerage/accounts'  # Try brokerage accounts endpoint
        ]
        
        accounts_response = None
        positions_response = None
        portfolio_response = None
        
        for endpoint in api_endpoints:
            try:
                # Try to get accounts list first
                accounts_response = schwab.get(f'https://api.schwabapi.com/{endpoint}', headers=headers)
                if accounts_response.status_code == 200:
                    accounts_data = accounts_response.json()
                    logger.debug(f"Successfully got accounts from {endpoint}")
                    
                    # If we have accounts, try to get positions and portfolio for each account
                    for account in accounts_data.get('accounts', []):
                        account_id = account.get('accountId')
                        if account_id:
                            try:
                                positions_response = schwab.get(
                                    f'https://api.schwabapi.com/{endpoint}/{account_id}/positions',
                                    headers=headers
                                )
                                portfolio_response = schwab.get(
                                    f'https://api.schwabapi.com/{endpoint}/{account_id}/portfolio',
                                    headers=headers
                                )
                                if positions_response.status_code == 200 or portfolio_response.status_code == 200:
                                    break
                            except Exception as e:
                                logger.warning(f"Error getting positions/portfolio for account {account_id}: {e}")
                    break
            except Exception as e:
                logger.warning(f"Error trying endpoint {endpoint}: {e}")
                continue
        
        return jsonify({
            "success": True,
            "message": "Successfully authenticated with Schwab",
            "error": {
                "positions_error": {
                    "status_code": positions_response.status_code if positions_response else None,
                    "response": positions_response.json() if positions_response else None,
                    "headers": dict(positions_response.headers) if positions_response else None
                } if positions_response else None,
                "accounts_error": {
                    "status_code": accounts_response.status_code if accounts_response else None,
                    "response": accounts_response.json() if accounts_response else None,
                    "headers": dict(accounts_response.headers) if accounts_response else None
                } if accounts_response else None,
                "portfolio_error": {
                    "status_code": portfolio_response.status_code if portfolio_response else None,
                    "response": portfolio_response.json() if portfolio_response else None,
                    "headers": dict(portfolio_response.headers) if portfolio_response else None
                } if portfolio_response else None,
                "token_info": {
                    "scope": token_response.get('scope'),
                    "token_type": token_response.get('token_type'),
                    "expires_in": token_response.get('expires_in'),
                    "client_correlid": client_correlid,
                    "id_token": token_response.get('id_token')
                }
            }
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
