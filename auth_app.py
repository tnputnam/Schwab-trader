from flask import Flask, session, redirect, request, jsonify, url_for, render_template
from requests_oauthlib import OAuth2Session
import os
import logging
import base64
import requests
from datetime import datetime, timedelta
import yfinance as yf
from flask_cors import CORS
from schwab_trader.utils.schwab_oauth import SchwabOAuth
from schwab_trader.routes.dashboard import bp as dashboard_bp
from strategy_tester import StrategyTester
from example_strategies import (
    moving_average_crossover_strategy,
    rsi_strategy,
    bollinger_bands_strategy,
    macd_strategy,
    volume_strategy,
    tesla_volume_analysis
)
import numpy as np
import pandas as pd
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='schwab_trader/templates',
    static_folder='schwab_trader/static'
)
CORS(app)
app.secret_key = 'your-secret-key-here'

# Simple test route
@app.route('/test')
def test():
    logger.info("Test route accessed")
    return "Test route working!"

@app.route('/test_alpha_vantage', methods=['GET'])
def test_alpha_vantage():
    """Test page for Alpha Vantage API"""
    logger.info("Accessing test_alpha_vantage route")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Template folder: {app.template_folder}")
    try:
        return render_template('test_alpha_vantage.html')
    except Exception as e:
        logger.error(f"Error rendering template: {str(e)}")
        return str(e), 500

@app.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage_api():
    """Test Alpha Vantage API endpoint"""
    logger.info("Accessing test_alpha_vantage_api route")
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL')
        
        logger.info(f"Testing Alpha Vantage API for symbol: {symbol}")
        
        # Get API key
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'error',
                'message': 'Alpha Vantage API key not found in environment'
            }), 400
        
        # Test different endpoints
        endpoints = {
            'TIME_SERIES_DAILY': f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}",
            'GLOBAL_QUOTE': f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}",
            'SYMBOL_SEARCH': f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={symbol}&apikey={api_key}"
        }
        
        results = {}
        for endpoint, url in endpoints.items():
            try:
                logger.info(f"Testing {endpoint} endpoint")
                response = requests.get(url, timeout=10)
                logger.info(f"Response status: {response.status_code}")
                logger.info(f"Response content: {response.text[:500]}")
                
                if response.status_code == 200:
                    data = response.json()
                    results[endpoint] = {
                        'status': 'success',
                        'data': data
                    }
                else:
                    results[endpoint] = {
                        'status': 'error',
                        'message': f"HTTP Error: {response.status_code}",
                        'response': response.text
                    }
            except Exception as e:
                results[endpoint] = {
                    'status': 'error',
                    'message': str(e)
                }
        
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error testing Alpha Vantage API: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/strategy_dashboard')
def strategy_dashboard():
    """Show strategy testing dashboard"""
    logger.info("Accessing strategy dashboard")
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('strategy_dashboard.html')

# Register blueprints
app.register_blueprint(dashboard_bp, url_prefix='/')

# Remove server name configuration to allow localhost access
# app.config['SERVER_NAME'] = 'b148-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app'

# Your Schwab API credentials
CLIENT_ID = "nuXZreDmdJzAsb4XGU24pArjpkJPltXB"
CLIENT_SECRET = "xzuIIEWzAs7nQd5A"

# Use HTTPS ngrok URL
REDIRECT_URI = "https://b148-2605-59c8-7260-b910-e13a-f44a-223d-42b6.ngrok-free.app/callback"

# Fixed URLs
AUTHORIZATION_BASE_URL = "https://api.schwabapi.com/v1/oauth/authorize"
TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

# Updated scope
SCOPES = ["api"]

# Initialize Schwab OAuth client
schwab = SchwabOAuth()

# Set the configuration
schwab.client_id = CLIENT_ID
schwab.client_secret = CLIENT_SECRET
schwab.redirect_uri = REDIRECT_URI
schwab.authorization_base_url = AUTHORIZATION_BASE_URL
schwab.token_url = TOKEN_URL
schwab.scopes = SCOPES

@app.route('/')
def index():
    """Display the main index page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Start OAuth login flow"""
    try:
        # Clear any existing session data
        session.clear()
        
        logger.debug("Starting login process")
        oauth = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES
        )
        
        # Generate a random state for security
        import secrets
        state = secrets.token_urlsafe(16)
        session['oauth_state'] = state
        
        auth_url, _ = oauth.authorization_url(
            AUTHORIZATION_BASE_URL,
            state=state
        )
        logger.debug(f"Generated authorization URL: {auth_url}")
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error in login: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/callback')
def callback():
    """Handle OAuth callback"""
    try:
        logger.debug("Received callback request")
        logger.debug(f"Request args: {request.args}")
        logger.debug(f"Request URL: {request.url}")
        
        # Verify state parameter
        state = request.args.get('state')
        if not state or state != session.get('oauth_state'):
            logger.error("Invalid state parameter")
            return jsonify({'error': 'Invalid state parameter'}), 400
        
        # Get authorization code
        auth_code = request.args.get('code')
        if not auth_code:
            logger.error("No authorization code received")
            return jsonify({'error': 'No authorization code'}), 400
            
        logger.debug(f"Authorization code received: {auth_code}")
        
        # Create new OAuth2Session instance for token exchange
        oauth = OAuth2Session(
            CLIENT_ID,
            redirect_uri=REDIRECT_URI,
            scope=SCOPES
        )
        
        # Exchange code for token
        logger.debug("Attempting to fetch token...")
        try:
            token = oauth.fetch_token(
                TOKEN_URL,
                authorization_response=request.url,
                client_secret=CLIENT_SECRET,
                include_client_id=True
            )
            logger.debug("Token fetch successful")
            logger.debug(f"Token data: {token}")
        except Exception as e:
            logger.error(f"Error fetching token: {str(e)}")
            return jsonify({'error': f'Failed to get token: {str(e)}'}), 401
            
        # Store token in session
        session['access_token'] = token
        logger.debug("Token stored in session")
        
        # Get account data
        logger.debug("Fetching account data")
        try:
            account_data = schwab.get_accounts(token)
            if not account_data:
                logger.error("Failed to get account data")
                return jsonify({'error': 'Failed to get account data'}), 500
                
            logger.debug(f"Account data received: {account_data}")
            
            # Store account data in session
            session['account_data'] = account_data
            logger.debug("Account data stored in session")
            
            # Get positions
            logger.debug("Fetching positions")
            positions = schwab.get_positions(token)
            logger.debug(f"Positions received: {positions}")
            
            # Store positions in session
            session['positions'] = positions
            logger.debug(f"Positions stored in session: {positions}")
            
            return redirect(url_for('dashboard'))
        except Exception as e:
            logger.error(f"Error getting account data: {str(e)}")
            return jsonify({'error': f'Failed to get account data: {str(e)}'}), 500
            
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/dashboard')
def dashboard():
    """Display account dashboard"""
    logger.debug("Accessing dashboard route")
    logger.debug(f"Session data: {dict(session)}")
    
    if 'access_token' not in session:
        logger.error("No access token in session, redirecting to login")
        return redirect(url_for('login'))
        
    account_data = session.get('account_data', {})
    positions = session.get('positions', [])
    
    logger.debug(f"Account data: {account_data}")
    logger.debug(f"Positions: {positions}")
    
    if not account_data:
        logger.error("No account data in session, redirecting to login")
        return redirect(url_for('login'))
        
    # Extract relevant account information
    account = account_data.get('securitiesAccount', {})
    current_balances = account.get('currentBalances', {})
    
    # Construct the market data URL
    market_data_url = f"https://{app.config['SERVER_NAME']}/api/market_data"
    
    account_info = {
        'account_number': account.get('accountNumber'),
        'account_type': account.get('type'),
        'cash_balance': current_balances.get('cashBalance', 0),
        'cash_available': current_balances.get('cashAvailableForTrading', 0),
        'total_value': current_balances.get('liquidationValue', 0),
        'long_market_value': current_balances.get('longMarketValue', 0),
        'positions': positions,
        'market_data_url': market_data_url
    }
    
    logger.debug(f"Account info being passed to template: {account_info}")
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
        'Bollinger Bands': bollinger_bands_strategy,
        'MACD': macd_strategy,
        'Volume': volume_strategy
    }
    
    for name, strategy in strategies.items():
        results[name] = tester.backtest_strategy(strategy, symbols, start_date, end_date)
    
    return jsonify({
        'status': 'success',
        'results': results
    })

@app.route('/paper_trade', methods=['POST'])
def paper_trade():
    """Run paper trading with selected strategy"""
    if 'access_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
        
    data = request.get_json()
    if not data or 'strategy' not in data or 'symbols' not in data:
        return jsonify({'error': 'Missing required parameters'}), 400
        
    # Get strategy function
    strategy_name = data['strategy']
    strategies = {
        'moving_average_crossover': moving_average_crossover_strategy,
        'rsi': rsi_strategy,
        'bollinger_bands': bollinger_bands_strategy,
        'macd': macd_strategy,
        'volume': volume_strategy
    }
    
    if strategy_name not in strategies:
        return jsonify({'error': 'Invalid strategy'}), 400
        
    # Initialize strategy tester and sync with Schwab account
    tester = StrategyTester()
    tester.sync_with_schwab(session['access_token'])
    
    # Run paper trading
    try:
        results = tester.paper_trade(strategies[strategy_name], data['symbols'])
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/market_data')
def get_market_data():
    """Get real-time market data for positions"""
    try:
        logger.debug("Market data endpoint called")
        logger.debug(f"Session data: {dict(session)}")
        
        if 'access_token' not in session:
            logger.error("No access token in session")
            return jsonify({'error': 'Not authenticated'}), 401
            
        positions = session.get('positions', [])
        logger.debug(f"Positions from session: {positions}")
        
        if not positions:
            logger.warning("No positions found in session")
            return jsonify({'error': 'No positions found'}), 404
            
        market_data = {}
        
        for position in positions:
            symbol = position.get('symbol')
            logger.debug(f"Processing position for symbol: {symbol}")
            
            if symbol:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    logger.debug(f"YFinance info for {symbol}: {info}")
                    
                    # Get historical data for technical indicators
                    hist = stock.history(period="1mo", interval="1d")
                    logger.debug(f"Historical data shape for {symbol}: {hist.shape}")
                    
                    # Calculate technical indicators
                    hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
                    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
                    
                    # Calculate RSI
                    delta = hist['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    hist['RSI'] = 100 - (100 / (1 + rs))
                    
                    # Calculate Bollinger Bands
                    hist['BB_middle'] = hist['Close'].rolling(window=20).mean()
                    hist['BB_std'] = hist['Close'].rolling(window=20).std()
                    hist['BB_upper'] = hist['BB_middle'] + (hist['BB_std'] * 2)
                    hist['BB_lower'] = hist['BB_middle'] - (hist['BB_std'] * 2)
                    
                    # Format historical data for chart
                    chart_data = {
                        'dates': hist.index.strftime('%Y-%m-%d').tolist(),
                        'close': hist['Close'].tolist(),
                        'sma_20': hist['SMA_20'].tolist(),
                        'sma_50': hist['SMA_50'].tolist(),
                        'bb_upper': hist['BB_upper'].tolist(),
                        'bb_lower': hist['BB_lower'].tolist(),
                        'rsi': hist['RSI'].tolist()
                    }
                    
                    market_data[symbol] = {
                        'current_price': info.get('regularMarketPrice', 0),
                        'change': info.get('regularMarketChange', 0),
                        'change_percent': info.get('regularMarketChangePercent', 0),
                        'volume': info.get('regularMarketVolume', 0),
                        'high': info.get('regularMarketDayHigh', 0),
                        'low': info.get('regularMarketDayLow', 0),
                        'bid': info.get('bid', 0),
                        'ask': info.get('ask', 0),
                        'bid_size': info.get('bidSize', 0),
                        'ask_size': info.get('askSize', 0),
                        'fifty_two_week_high': info.get('fiftyTwoWeekHigh', 0),
                        'fifty_two_week_low': info.get('fiftyTwoWeekLow', 0),
                        'pe_ratio': info.get('trailingPE', 0),
                        'market_cap': info.get('marketCap', 0),
                        'chart_data': chart_data
                    }
                    logger.debug(f"Market data for {symbol}: {market_data[symbol]}")
                except Exception as e:
                    logger.error(f"Error getting market data for {symbol}: {str(e)}")
                    market_data[symbol] = {'error': str(e)}
        
        logger.debug(f"Final market data response: {market_data}")
        return jsonify(market_data)
    except Exception as e:
        logger.error(f"Unexpected error in market data endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tesla_dashboard')
def tesla_dashboard():
    """Show Tesla analysis dashboard without authentication"""
    return render_template('strategy_dashboard.html')

@app.route('/tesla_analysis')
def tesla_analysis_page():
    """Display the Tesla analysis page."""
    return render_template('tesla_analysis.html')

@app.route('/volatile_stocks')
def volatile_stocks():
    """Display the volatile stocks page"""
    return render_template('volatile_stocks.html')

@app.route('/api/tesla_analysis')
def tesla_analysis():
    """Analyze Tesla's volume patterns and their impact on price"""
    try:
        # Get Tesla's historical data
        tsla = yf.Ticker("TSLA")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Last 30 days
        data = tsla.history(start=start_date, end=end_date)
        
        # Calculate monthly average volume
        monthly_avg_volume = data['Volume'].mean()
        
        # Identify high volume days (15% above average)
        high_volume_mask = data['Volume'] > (monthly_avg_volume * 1.15)
        high_volume_days = data[high_volume_mask]
        
        # Calculate price changes during high volume days
        price_changes = []
        for idx, day in high_volume_days.iterrows():
            next_day_idx = data.index.get_loc(idx) + 1
            if next_day_idx < len(data):
                next_day = data.iloc[next_day_idx]
                price_change = ((next_day['Close'] - day['Close']) / day['Close']) * 100
                price_changes.append({
                    'date': idx.strftime('%Y-%m-%d'),
                    'volume': day['Volume'],
                    'close_price': day['Close'],
                    'price_change': price_change
                })
        
        # Calculate volume-price correlation
        volume_correlation = data['Volume'].corr(data['Close'].pct_change())
        
        analysis = {
            'monthly_avg_volume': monthly_avg_volume,
            'high_volume_days': len(high_volume_days),
            'price_changes': price_changes,
            'volume_correlation': volume_correlation,
            'high_volume_days_data': high_volume_days[['Volume', 'Close']].to_dict('records')
        }
        
        return jsonify({
            'status': 'success',
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error in Tesla analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/auto_trading')
def auto_trading_dashboard():
    """Show auto trading dashboard"""
    if 'access_token' not in session:
        return redirect(url_for('login'))
    return render_template('auto_trading.html')

@app.route('/api/start_auto_trading', methods=['POST'])
def start_auto_trading():
    """Start auto trading with specified strategy and budget"""
    try:
        if 'access_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.get_json()
        if not data or 'strategy' not in data or 'symbols' not in data or 'budget' not in data:
            return jsonify({'error': 'Missing required parameters'}), 400
            
        # Get strategy function
        strategy_name = data['strategy']
        strategies = {
            'moving_average_crossover': moving_average_crossover_strategy,
            'rsi': rsi_strategy,
            'bollinger_bands': bollinger_bands_strategy,
            'macd': macd_strategy,
            'volume': volume_strategy
        }
        
        if strategy_name not in strategies:
            return jsonify({'error': 'Invalid strategy'}), 400
            
        # Initialize strategy tester
        tester = StrategyTester()
        tester.sync_with_schwab(session['access_token'])
        
        # Set budget
        tester.set_budget(data['budget'])
        
        # Start auto trading in a separate thread
        import threading
        thread = threading.Thread(
            target=tester.run_auto_trading,
            args=(strategies[strategy_name], data['symbols'])
        )
        thread.daemon = True
        thread.start()
        
        # Store trading state in session
        session['trading_active'] = True
        session['trading_strategy'] = strategy_name
        session['trading_symbols'] = data['symbols']
        session['trading_budget'] = data['budget']
        
        return jsonify({
            'status': 'success',
            'message': 'Auto trading started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting auto trading: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stop_auto_trading', methods=['POST'])
def stop_auto_trading():
    """Stop auto trading"""
    try:
        if 'access_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        # Clear trading state from session
        session.pop('trading_active', None)
        session.pop('trading_strategy', None)
        session.pop('trading_symbols', None)
        session.pop('trading_budget', None)
        
        return jsonify({
            'status': 'success',
            'message': 'Auto trading stopped successfully'
        })
        
    except Exception as e:
        logger.error(f"Error stopping auto trading: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/trading_status', methods=['GET'])
def get_trading_status():
    """Get current trading status and performance"""
    try:
        if 'access_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        # Initialize strategy tester
        tester = StrategyTester()
        tester.sync_with_schwab(session['access_token'])
        
        # Get current status
        status = {
            'active': session.get('trading_active', False),
            'strategy': session.get('trading_strategy', None),
            'symbols': session.get('trading_symbols', []),
            'budget': session.get('trading_budget', 0),
            'current_balance': tester.get_current_balance(),
            'active_positions': tester.get_active_positions(),
            'trade_history': tester.get_trade_history()
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting trading status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/top_volatile_stocks')
def top_volatile_stocks():
    """Get top 10 most volatile stocks with volume analysis"""
    try:
        # List of major stocks to analyze
        symbols = ['SPY', 'QQQ', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD']
        
        results = []
        for symbol in symbols:
            try:
                stock = yf.Ticker(symbol)
                # Get 1 year of data
                data = stock.history(period="1y", interval="1d")
                
                if not data.empty:
                    # Calculate volatility (standard deviation of daily returns)
                    daily_returns = data['Close'].pct_change()
                    volatility = daily_returns.std() * np.sqrt(252)  # Annualized volatility
                    
                    # Calculate volume metrics
                    current_volume = data['Volume'].iloc[-1]
                    avg_volume = data['Volume'].mean()
                    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
                    
                    # Calculate recent price change
                    price_change = ((data['Close'].iloc[-1] - data['Close'].iloc[0]) / data['Close'].iloc[0]) * 100
                    
                    # Calculate technical indicators
                    # Moving Averages
                    data['SMA_20'] = data['Close'].rolling(window=20).mean()
                    data['SMA_50'] = data['Close'].rolling(window=50).mean()
                    data['SMA_200'] = data['Close'].rolling(window=200).mean()
                    
                    # RSI
                    delta = data['Close'].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    data['RSI'] = 100 - (100 / (1 + rs))
                    
                    # Bollinger Bands
                    data['BB_middle'] = data['Close'].rolling(window=20).mean()
                    data['BB_std'] = data['Close'].rolling(window=20).std()
                    data['BB_upper'] = data['BB_middle'] + (data['BB_std'] * 2)
                    data['BB_lower'] = data['BB_middle'] - (data['BB_std'] * 2)
                    
                    # MACD
                    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
                    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
                    data['MACD'] = exp1 - exp2
                    data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()
                    
                    # Stochastic Oscillator
                    data['Lowest_14'] = data['Low'].rolling(window=14).min()
                    data['Highest_14'] = data['High'].rolling(window=14).max()
                    data['%K'] = 100 * ((data['Close'] - data['Lowest_14']) / (data['Highest_14'] - data['Lowest_14']))
                    data['%D'] = data['%K'].rolling(window=3).mean()
                    
                    # ADX (Average Directional Index)
                    data['+DM'] = data['High'].diff()
                    data['-DM'] = data['Low'].diff()
                    data['+DM'] = data['+DM'].where(data['+DM'] > 0, 0)
                    data['-DM'] = data['-DM'].where(data['-DM'] > 0, 0)
                    data['TR'] = data['High'] - data['Low']
                    data['+DI'] = 100 * (data['+DM'].rolling(window=14).mean() / data['TR'].rolling(window=14).mean())
                    data['-DI'] = 100 * (data['-DM'].rolling(window=14).mean() / data['TR'].rolling(window=14).mean())
                    data['ADX'] = 100 * abs((data['+DI'] - data['-DI']) / (data['+DI'] + data['-DI'])).rolling(window=14).mean()
                    
                    # Get current price and market cap
                    info = stock.info
                    current_price = info.get('regularMarketPrice', 0)
                    market_cap = info.get('marketCap', 0)
                    
                    # Get news
                    news = stock.news
                    formatted_news = []
                    for item in news:
                        formatted_news.append({
                            'title': item.get('title', ''),
                            'link': item.get('link', ''),
                            'publisher': item.get('publisher', ''),
                            'published': item.get('published', ''),
                            'summary': item.get('summary', '')
                        })
                    
                    # Format historical data for chart
                    volume_history = {
                        'dates': data.index.strftime('%Y-%m-%d').tolist(),
                        'volumes': data['Volume'].tolist(),
                        'prices': data['Close'].tolist(),
                        'sma_20': data['SMA_20'].tolist(),
                        'sma_50': data['SMA_50'].tolist(),
                        'sma_200': data['SMA_200'].tolist(),
                        'bb_upper': data['BB_upper'].tolist(),
                        'bb_lower': data['BB_lower'].tolist(),
                        'rsi': data['RSI'].tolist(),
                        'macd': data['MACD'].tolist(),
                        'signal_line': data['Signal_Line'].tolist(),
                        'stochastic_k': data['%K'].tolist(),
                        'stochastic_d': data['%D'].tolist(),
                        'adx': data['ADX'].tolist(),
                        'plus_di': data['+DI'].tolist(),
                        'minus_di': data['-DI'].tolist()
                    }
                    
                    # Calculate current indicator values
                    current_indicators = {
                        'rsi': data['RSI'].iloc[-1],
                        'macd': data['MACD'].iloc[-1],
                        'signal_line': data['Signal_Line'].iloc[-1],
                        'bb_position': (current_price - data['BB_lower'].iloc[-1]) / (data['BB_upper'].iloc[-1] - data['BB_lower'].iloc[-1]) * 100,
                        'sma_20_position': (current_price - data['SMA_20'].iloc[-1]) / data['SMA_20'].iloc[-1] * 100,
                        'sma_50_position': (current_price - data['SMA_50'].iloc[-1]) / data['SMA_50'].iloc[-1] * 100,
                        'sma_200_position': (current_price - data['SMA_200'].iloc[-1]) / data['SMA_200'].iloc[-1] * 100,
                        'stochastic_k': data['%K'].iloc[-1],
                        'stochastic_d': data['%D'].iloc[-1],
                        'adx': data['ADX'].iloc[-1],
                        'plus_di': data['+DI'].iloc[-1],
                        'minus_di': data['-DI'].iloc[-1]
                    }
                    
                    results.append({
                        'symbol': symbol,
                        'volatility': volatility * 100,  # Convert to percentage
                        'current_price': current_price,
                        'price_change': price_change,
                        'market_cap': market_cap,
                        'current_volume': current_volume,
                        'avg_volume': avg_volume,
                        'volume_ratio': volume_ratio,
                        'volume_history': volume_history,
                        'current_indicators': current_indicators,
                        'news': formatted_news
                    })
            
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        # Sort by volatility (highest first)
        results.sort(key=lambda x: x['volatility'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'stocks': results[:10]  # Return top 10 most volatile
        })
        
    except Exception as e:
        logger.error(f"Error in volatile stocks analysis: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/analyze_volatility')
def analyze_volatility():
    try:
        # Get list of stocks to analyze
        stocks = ['TSLA', 'AAPL', 'MSFT', 'AMZN', 'GOOGL', 'META', 'NVDA', 'AMD', 'INTC', 'QCOM']
        results = []
        
        for symbol in stocks:
            try:
                # Get stock data
                stock = yf.Ticker(symbol)
                hist = stock.history(period='1mo')
                
                # Calculate volatility
                returns = hist['Close'].pct_change()
                volatility = returns.std() * (252 ** 0.5)  # Annualized volatility
                
                # Get current indicators
                current_price = hist['Close'][-1]
                current_volume = hist['Volume'][-1]
                current_indicators = {
                    'price': current_price,
                    'volume': current_volume,
                    'volatility': volatility
                }
                
                # Get news
                news = stock.news
                formatted_news = [{
                    'title': item['title'],
                    'link': item['link'],
                    'date': item['publisher']['publishedAt']
                } for item in news[:5]]  # Get top 5 news items
                
                results.append({
                    'symbol': symbol,
                    'volatility': volatility,
                    'current_indicators': current_indicators,
                    'news': formatted_news
                })
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                continue
        
        results.sort(key=lambda x: x['volatility'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'stocks': results[:10]  # Return top 10 most volatile
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_volatility: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/portfolio')
def portfolio():
    """Display the portfolio page"""
    return render_template('portfolio.html')

@app.route('/news')
def news():
    """Display the news page"""
    return render_template('news.html')

@app.route('/trading')
def trading():
    """Display the trading page"""
    return render_template('trading.html')

@app.route('/compare')
def compare():
    """Display the compare page"""
    return render_template('compare.html')

@app.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis page"""
    return render_template('volume_analysis.html')

@app.route('/auto_trading')
def auto_trading():
    """Display the auto trading page"""
    return render_template('auto_trading.html')

@app.route('/tesla_analysis')
def tesla_analysis():
    """Display the Tesla analysis page"""
    return render_template('tesla_analysis.html')

@app.route('/dashboard/api/run_backtest', methods=['POST'])
def run_backtest():
    """Run backtest for specified symbols and date range"""
    try:
        data = request.get_json()
        symbols = [s.strip() for s in data['symbols'].split(',')]
        start_date = data['startDate']
        end_date = data['endDate']
        
        logger.info(f"Starting backtest for symbols: {symbols}")
        logger.info(f"Date range: {start_date} to {end_date}")
        
        # Initialize strategy tester
        tester = StrategyTester()
        
        # Test strategies
        results = []
        strategies = {
            'Moving Average Crossover': moving_average_crossover_strategy,
            'RSI': rsi_strategy,
            'Bollinger Bands': bollinger_bands_strategy,
            'MACD': macd_strategy,
            'Volume': volume_strategy
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Processing symbol: {symbol}")
                hist = None
                
                # Try Alpha Vantage first
                try:
                    logger.info(f"Attempting to fetch data from Alpha Vantage for {symbol}")
                    api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
                    if not api_key:
                        raise Exception("Alpha Vantage API key not found in environment")
                    
                    # First try the TIME_SERIES_DAILY endpoint
                    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=full&apikey={api_key}"
                    logger.info(f"Alpha Vantage URL: {url}")
                    
                    # Add a timeout and retry mechanism
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            response = requests.get(url, timeout=10)
                            logger.info(f"Alpha Vantage response status: {response.status_code}")
                            logger.info(f"Alpha Vantage response content: {response.text[:200]}")
                            
                            if response.status_code == 200:
                                break
                            elif response.status_code == 429:  # Rate limit
                                if attempt < max_retries - 1:
                                    logger.warning(f"Rate limited, waiting before retry {attempt + 1}")
                                    time.sleep(5)  # Wait 5 seconds before retry
                                    continue
                            else:
                                raise Exception(f"HTTP Error: {response.status_code}")
                        except requests.Timeout:
                            if attempt < max_retries - 1:
                                logger.warning(f"Timeout, retrying {attempt + 1}")
                                continue
                            raise
                    
                    if not response.text.strip():
                        raise Exception("Empty response from Alpha Vantage")
                    
                    data_av = response.json()
                    logger.info(f"Alpha Vantage response keys: {list(data_av.keys())}")
                    
                    if 'Error Message' in data_av:
                        error_msg = data_av['Error Message']
                        logger.error(f"Alpha Vantage error for {symbol}: {error_msg}")
                        raise Exception(error_msg)
                    
                    if 'Note' in data_av:
                        logger.warning(f"Alpha Vantage note for {symbol}: {data_av['Note']}")
                    
                    # Convert Alpha Vantage data to DataFrame
                    time_series = data_av.get('Time Series (Daily)', {})
                    if not time_series:
                        logger.error(f"No time series data found for {symbol}")
                        raise Exception("No data available from Alpha Vantage")
                    
                    logger.info(f"Found {len(time_series)} days of data for {symbol}")
                    
                    # Create DataFrame with proper column names
                    df = pd.DataFrame.from_dict(time_series, orient='index')
                    df.index = pd.to_datetime(df.index)
                    df = df.sort_index()
                    
                    # Rename columns to match expected format
                    column_mapping = {
                        '1. open': 'Open',
                        '2. high': 'High',
                        '3. low': 'Low',
                        '4. close': 'Close',
                        '5. volume': 'Volume'
                    }
                    df = df.rename(columns=column_mapping)
                    
                    # Convert to numeric values
                    for col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    # Filter by date range
                    start_dt = pd.to_datetime(start_date)
                    end_dt = pd.to_datetime(end_date)
                    hist = df[(df.index >= start_dt) & (df.index <= end_dt)]
                    
                    if hist.empty:
                        raise Exception("No data available for the specified date range")
                    
                    logger.info(f"Filtered data points for {symbol}: {len(hist)}")
                    
                except Exception as av_error:
                    logger.error(f"Alpha Vantage failed for {symbol}: {str(av_error)}")
                    raise Exception(f"Failed to fetch data from Alpha Vantage: {str(av_error)}")
                
                if hist is None or hist.empty:
                    logger.warning(f"No data found for {symbol} in the specified date range")
                    results.append({
                        'symbol': symbol,
                        'error': f"No historical data found for the specified date range"
                    })
                    continue
                
                for strategy_name, strategy in strategies.items():
                    try:
                        logger.info(f"Running {strategy_name} for {symbol}")
                        result = tester.backtest_strategy(strategy, [symbol], start_date, end_date)
                        results.append({
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'initialPrice': result['portfolio_value'][0],
                            'finalPrice': result['portfolio_value'][-1],
                            'totalReturn': result['metrics']['total_return'],
                            'sharpeRatio': result['metrics']['sharpe_ratio'],
                            'maxDrawdown': result['metrics']['max_drawdown'],
                            'numTrades': result['metrics']['num_trades']
                        })
                        logger.info(f"Successfully completed {strategy_name} for {symbol}")
                    except Exception as e:
                        logger.error(f"Error backtesting {strategy_name} for {symbol}: {str(e)}")
                        results.append({
                            'symbol': symbol,
                            'strategy': strategy_name,
                            'error': str(e)
                        })
                        continue
            except Exception as e:
                logger.error(f"Error processing {symbol}: {str(e)}")
                results.append({
                    'symbol': symbol,
                    'error': f"Failed to process symbol: {str(e)}"
                })
                continue
        
        if not results:
            logger.error("No valid results found for any symbols")
            return jsonify({
                'status': 'error',
                'message': 'No valid results found for any symbols'
            }), 400
        
        logger.info(f"Backtest completed successfully with {len(results)} results")
        return jsonify({
            'status': 'success',
            'results': results
        })
        
    except Exception as e:
        logger.error(f"Error in backtest: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True)
