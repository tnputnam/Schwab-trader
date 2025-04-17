from flask import Flask, session, redirect, request, jsonify
from requests_oauthlib import OAuth2Session
import os
import logging
import base64
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

# Use HTTPS ngrok URL
REDIRECT_URI = "https://fff5-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app/callback"

# Fixed URLs
AUTHORIZATION_BASE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# Updated scope
SCOPES = ["api"]

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
    
    # Construct authorization URL directly
    auth_url = f"{AUTHORIZATION_BASE_URL}?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
    logger.debug(f"Generated Authorization URL: {auth_url}")
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    logger.debug("Received callback")
    try:
        # Get the authorization code from the callback
        auth_code = request.args.get('code', '')
        if '@' not in auth_code:
            auth_code = f"{auth_code}@"
        
        logger.debug(f"Authorization code: {auth_code}")
        
        # Construct credentials
        credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
        base64_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
        
        # Construct headers and payload for token request
        token_headers = {
            "Authorization": f"Basic {base64_credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        token_payload = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": REDIRECT_URI
        }
        
        # Get token
        token_response = requests.post(
            url=TOKEN_URL,
            headers=token_headers,
            data=token_payload
        )
        
        token_data = token_response.json()
        logger.debug(f"Token response: {token_data}")
        
        # Store token
        session['oauth_token'] = token_data
        
        # Get client correlation ID from token response headers
        client_correlid = token_response.headers.get('Schwab-Client-Correlid')
        if not client_correlid:
            # Try to get it from the token response body
            client_correlid = token_data.get('client_correlid', '')
        
        logger.debug(f"Client correlation ID: {client_correlid}")
        
        # API headers for subsequent requests
        api_headers = {
            'Accept': 'application/json',
            'Authorization': f"Bearer {token_data['access_token']}",
            'X-Authorization': f"Bearer {token_data['access_token']}",
            'Schwab-Client-Correlid': client_correlid,
            'Origin': REDIRECT_URI.rsplit('/', 1)[0]
        }
        
        # First get the account numbers
        accounts_response = requests.get(
            'https://api.schwabapi.com/v1/accounts/accountNumbers',
            headers=api_headers
        )
        
        if accounts_response.status_code == 200:
            accounts_data = accounts_response.json()
            logger.debug(f"Accounts data: {accounts_data}")
            
            # Try to get positions and portfolio for each account
            results = []
            for account_number in accounts_data.get('accountNumbers', []):
                # Get account details
                account_response = requests.get(
                    f'https://api.schwabapi.com/v1/accounts/{account_number}',
                    headers=api_headers
                )
                
                # Get positions
                positions_response = requests.get(
                    f'https://api.schwabapi.com/v1/accounts/{account_number}/positions',
                    headers=api_headers
                )
                
                # Get portfolio
                portfolio_response = requests.get(
                    f'https://api.schwabapi.com/v1/accounts/{account_number}/portfolio',
                    headers=api_headers
                )
                
                results.append({
                    'account_number': account_number,
                    'account_details': account_response.json() if account_response.status_code == 200 else None,
                    'positions': positions_response.json() if positions_response.status_code == 200 else None,
                    'portfolio': portfolio_response.json() if portfolio_response.status_code == 200 else None
                })
            
            return jsonify({
                "success": True,
                "message": "Successfully authenticated with Schwab",
                "accounts": accounts_data,
                "results": results,
                "debug_info": {
                    "client_correlid": client_correlid,
                    "headers_used": api_headers
                }
            })
        
        # If we get here, return error information
        return jsonify({
            "success": True,
            "message": "Successfully authenticated with Schwab",
            "error": {
                "accounts_error": {
                    "status_code": accounts_response.status_code,
                    "response": accounts_response.json() if accounts_response.status_code != 404 else None,
                    "headers": dict(accounts_response.headers)
                },
                "token_info": {
                    "scope": token_data.get('scope'),
                    "token_type": token_data.get('token_type'),
                    "expires_in": token_data.get('expires_in'),
                    "client_correlid": client_correlid,
                    "access_token": token_data.get('access_token')
                },
                "debug_info": {
                    "headers_used": api_headers,
                    "token_response_headers": dict(token_response.headers)
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
