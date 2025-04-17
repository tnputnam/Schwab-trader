from flask import Flask, session, redirect, request, jsonify, url_for, render_template
from requests_oauthlib import OAuth2Session
import os
import logging
import base64
import requests
from datetime import datetime, timedelta
from strategy_tester import StrategyTester
from example_strategies import (
    moving_average_crossover_strategy,
    rsi_strategy,
    bollinger_bands_strategy
)

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
        session['access_token'] = token_data['access_token']
        
        # Get client correlation ID from token response headers
        client_correlid = token_response.headers.get('Schwab-Client-Correlid')
        if not client_correlid:
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
        
        # Get account details
        accounts_url = "https://api.schwabapi.com/trader/v1/accounts"
        accounts_response = requests.get(accounts_url, headers=api_headers)
        
        if accounts_response.status_code == 200:
            accounts_data = accounts_response.json()
            if accounts_data and isinstance(accounts_data, list):
                account = accounts_data[0]  # Get first account
                session['account_data'] = account
                
                # Get positions if available
                account_number = account['securitiesAccount']['accountNumber']
                positions_url = f"https://api.schwabapi.com/trader/v1/accounts/{account_number}/positions"
                positions_response = requests.get(positions_url, headers=api_headers)
                
                if positions_response.status_code == 200:
                    session['positions'] = positions_response.json()
                else:
                    session['positions'] = []
                    logger.warning(f"Could not fetch positions: {positions_response.status_code}")
                
                return redirect(url_for('dashboard'))
            else:
                return jsonify({
                    "success": False,
                    "error": "No accounts found"
                }), 404
        else:
            return jsonify({
                "success": False,
                "error": f"Failed to get accounts: {accounts_response.status_code}"
            }), accounts_response.status_code
            
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/dashboard')
def dashboard():
    """Display account dashboard"""
    if 'access_token' not in session:
        return redirect(url_for('login'))
        
    account_data = session.get('account_data', {})
    positions = session.get('positions', [])
    
    if not account_data:
        return redirect(url_for('login'))
        
    # Extract relevant account information
    account = account_data.get('securitiesAccount', {})
    current_balances = account.get('currentBalances', {})
    
    account_info = {
        'account_number': account.get('accountNumber'),
        'account_type': account.get('type'),
        'cash_balance': current_balances.get('cashBalance', 0),
        'cash_available': current_balances.get('cashAvailableForTrading', 0),
        'total_value': current_balances.get('liquidationValue', 0),
        'long_market_value': current_balances.get('longMarketValue', 0),
        'positions': positions
    }
    
    return render_template('dashboard.html', account=account_info)

@app.route('/test_strategies', methods=['GET'])
def test_strategies():
    """Test different trading strategies"""
    if 'access_token' not in session:
        return redirect(url_for('login'))
        
    # Initialize strategy tester and sync with Schwab account
    tester = StrategyTester()
    tester.sync_with_schwab(session['access_token'])
    
    # Define test parameters
    symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL']
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')
    
    # Test strategies
    results = {}
    strategies = {
        'Moving Average Crossover': moving_average_crossover_strategy,
        'RSI': rsi_strategy,
        'Bollinger Bands': bollinger_bands_strategy
    }
    
    for name, strategy in strategies.items():
        tester = StrategyTester()
        tester.sync_with_schwab(session['access_token'])
        results[name] = tester.run_strategy(strategy, symbols, start_date, end_date)
    
    return jsonify({
        'status': 'success',
        'results': results
    })

@app.route('/strategy_dashboard')
def strategy_dashboard():
    """Show strategy testing dashboard"""
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('strategy_dashboard.html')

if __name__ == '__main__':
    # For development only
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    logger.info("Starting Flask app...")
    logger.info(f"Using Authorization URL: {AUTHORIZATION_BASE_URL}")
    logger.info(f"Using Token URL: {TOKEN_URL}")
    logger.info(f"Using Scopes: {SCOPES}")
    app.run(host='0.0.0.0', port=5000, debug=True)
