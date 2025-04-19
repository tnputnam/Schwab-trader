from flask import Flask, session, redirect, request, jsonify, url_for, render_template
from requests_oauthlib import OAuth2Session
from flask_socketio import SocketIO, emit
from flask_migrate import Migrate
import os
import logging
import base64
import requests
from datetime import datetime, timedelta
import yfinance as yf
from flask_cors import CORS
from schwab_trader.utils.schwab_oauth import SchwabOAuth
from schwab_trader.routes.dashboard import bp as dashboard_bp
from schwab_trader.database import db
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
import asyncio
from typing import List
from types import SimpleNamespace

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='schwab_trader/templates',
    static_folder='schwab_trader/static'
)
CORS(app)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_key_123')

# Load configuration
app.config.from_object('schwab_trader.config.Config')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///schwab_trader.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

socketio = SocketIO(app, cors_allowed_origins="*")

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    def connect(self, sid):
        self.active_connections.add(sid)

    def disconnect(self, sid):
        self.active_connections.discard(sid)

    def broadcast(self, message):
        for sid in self.active_connections:
            socketio.emit('message', message, room=sid)

manager = ConnectionManager()

# Schwab OAuth routes
@app.route('/auth/schwab')
def schwab_auth():
    """Start the Schwab OAuth flow."""
    try:
        schwab = SchwabOAuth()
        auth_url = schwab.get_authorization_url()
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error starting Schwab auth: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/auth/callback')
def schwab_callback():
    """Handle the OAuth callback from Schwab."""
    try:
        schwab = SchwabOAuth()
        token = schwab.fetch_token(request.url)
        
        if token:
            # Store the token in the session
            session['schwab_token'] = token
            
            # Get user's accounts
            accounts = schwab.get_accounts()
            if accounts:
                session['schwab_accounts'] = accounts
                return redirect(url_for('dashboard.index'))
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to get accounts'
                }), 500
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to get token'
            }), 500
    except Exception as e:
        logger.error(f"Error in Schwab callback: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/auth/logout')
def schwab_logout():
    """Log out from Schwab."""
    session.pop('schwab_token', None)
    session.pop('schwab_accounts', None)
    return redirect(url_for('root.index'))

# WebSocket event handlers
@socketio.on('connect')
def handle_connect():
    manager.connect(request.sid)
    logger.info(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    manager.disconnect(request.sid)
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    symbols = data.get('symbols', [])
    if symbols:
        logger.info(f"Client {request.sid} subscribed to symbols: {symbols}")
        # Start monitoring these symbols
        asyncio.create_task(monitor_symbols(symbols))

# Background task to monitor symbols
async def monitor_symbols(symbols: List[str]):
    while True:
        try:
            for symbol in symbols:
                stock = yf.Ticker(symbol)
                data = stock.history(period="1d", interval="1m")
                if not data.empty:
                    latest = data.iloc[-1]
                    message = {
                        'symbol': symbol,
                        'price': latest['Close'],
                        'volume': latest['Volume'],
                        'timestamp': datetime.now().isoformat()
                    }
                    manager.broadcast(message)
            await asyncio.sleep(60)  # Update every minute
        except Exception as e:
            logger.error(f"Error monitoring symbols: {str(e)}")
            await asyncio.sleep(60)  # Wait before retrying

@app.route('/')
def index():
    """Display the main index page"""
    return render_template('index.html')

@app.route('/login')
def login():
    """Automatically redirect to dashboard"""
    return redirect(url_for('dashboard.index'))

@app.route('/dashboard')
def dashboard():
    """Display the main dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('market_dashboard.html')

@app.route('/dashboard/strategies')
def strategies_dashboard():
    """Display the strategies dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('strategy_dashboard.html')

@app.route('/dashboard/analysis')
def analysis_dashboard():
    """Display the analysis dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('analysis_dashboard.html')

@app.route('/dashboard/alerts')
def alerts_dashboard():
    """Display the alerts dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('alerts_dashboard.html')

@app.route('/dashboard/watchlist')
def watchlist_dashboard():
    """Display the watchlist dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('watchlist_dashboard.html')

@app.route('/portfolio')
def portfolio():
    """Display the portfolio page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
        
    try:
        schwab = SchwabOAuth()
        accounts = session.get('schwab_accounts', [])
        
        if not accounts:
            accounts = schwab.get_accounts()
            if accounts:
                session['schwab_accounts'] = accounts
        
        positions = []
        for account in accounts:
            account_positions = schwab.get_positions(account['accountNumber'])
            if account_positions:
                positions.extend(account_positions)
        
        # Calculate portfolio totals
        total_value = sum(pos['marketValue'] for pos in positions)
        total_change = sum(pos.get('currentDayProfitLoss', 0) for pos in positions)
        total_change_percent = (total_change / (total_value - total_change)) * 100 if total_value > 0 else 0
        
        portfolio = {
            'updated_at': datetime.now(),
            'total_value': total_value,
            'cash_value': sum(acc.get('currentBalances', {}).get('cashBalance', 0) for acc in accounts),
            'day_change': total_change,
            'day_change_percent': total_change_percent,
            'total_gain': sum(pos.get('unrealizedProfitLoss', 0) for pos in positions),
            'total_gain_percent': sum(pos.get('unrealizedProfitLossPercentage', 0) for pos in positions)
        }
        
        return render_template('portfolio_dashboard.html',
                             portfolio=SimpleNamespace(**portfolio),
                             positions=positions)
                             
    except Exception as e:
        logger.error(f"Error loading portfolio: {str(e)}")
        return render_template('portfolio_dashboard.html',
                             portfolio=SimpleNamespace(updated_at=datetime.now(),
                                                     total_value=0.00,
                                                     cash_value=0.00,
                                                     day_change=0.00,
                                                     day_change_percent=0.00,
                                                     total_gain=0.00,
                                                     total_gain_percent=0.00),
                             positions=[])

@app.route('/news')
def news():
    """Display the news page"""
    return render_template('news.html')

@app.route('/trading')
def trading():
    """Display the trading page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('trading_dashboard.html')

@app.route('/compare')
def compare():
    """Display the compare page"""
    return render_template('compare.html')

@app.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis page"""
    return render_template('tesla_dashboard.html')

@app.route('/dashboard/api/paper_trade', methods=['POST'])
def paper_trade():
    """Run paper trading with selected strategy"""
    if 'schwab_token' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
        
    try:
        data = request.get_json()
        if not data or 'strategy' not in data or 'symbols' not in data:
            return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400
            
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
            return jsonify({'status': 'error', 'message': 'Invalid strategy'}), 400
            
        # Initialize strategy tester and sync with Schwab account
        tester = StrategyTester()
        tester.sync_with_schwab(session['schwab_token'])
        
        # Run paper trading
        try:
            results = tester.paper_trade(strategies[strategy_name], data['symbols'])
            
            # Format results for frontend
            formatted_results = {
                'positions': {},
                'trades': []
            }
            
            # Format positions
            for symbol, position in results['positions'].items():
                formatted_results['positions'][symbol] = {
                    'quantity': position['quantity'],
                    'average_price': position['average_price']
                }
            
            # Format trades
            for trade in results['trades']:
                formatted_results['trades'].append({
                    'date': trade['date'].isoformat(),
                    'symbol': trade['symbol'],
                    'action': trade['action'],
                    'quantity': trade['quantity'],
                    'price': trade['price'],
                    'profit': trade.get('profit', None)
                })
            
            return jsonify({
                'status': 'success',
                'results': formatted_results
            })
            
        except Exception as e:
            logger.error(f"Error in paper trading: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Error in paper trading route: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/dashboard/api/search_symbols', methods=['POST'])
def search_symbols():
    """Search for symbols or company names"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip().upper()
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query is required'
            }), 400
        
        # Try Alpha Vantage first
        try:
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                raise Exception("Alpha Vantage API key not found")
            
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'bestMatches' in data:
                    results = []
                    for match in data['bestMatches']:
                        results.append({
                            'symbol': match['1. symbol'],
                            'name': match['2. name'],
                            'type': match['3. type'],
                            'region': match['4. region']
                        })
                    return jsonify({
                        'status': 'success',
                        'results': results
                    })
        except Exception as e:
            logger.warning(f"Alpha Vantage search failed: {str(e)}")
        
        # Fallback to yfinance
        try:
            # Get list of major stocks
            major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'QCOM']
            results = []
            
            for symbol in major_stocks:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    name = info.get('longName', '')
                    
                    if query in symbol or query in name.upper():
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'type': info.get('quoteType', ''),
                            'region': info.get('region', '')
                        })
                except:
                    continue
            
            return jsonify({
                'status': 'success',
                'results': results
            })
        except Exception as e:
            logger.error(f"yfinance search failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to search symbols'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in symbol search: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Alpha Vantage testing routes
@app.route('/test_alpha_vantage')
def test_alpha_vantage():
    try:
        return render_template('test_alpha_vantage.html')
    except Exception as e:
        return str(e), 500

@app.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage_api():
    """Test Alpha Vantage API endpoint"""
    logger.info("Testing Alpha Vantage API")
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL')
        
        # Get API key
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            logger.error("Alpha Vantage API key not found")
            return jsonify({
                'status': 'error',
                'message': 'Alpha Vantage API key not found in environment'
            }), 400
        
        logger.info(f"Testing Alpha Vantage API for symbol: {symbol}")
        logger.info(f"Using API key: {api_key[:5]}...")
        
        # Test TIME_SERIES_DAILY endpoint
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}"
        logger.info(f"Request URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return jsonify({
                        'status': 'error',
                        'message': data['Error Message']
                    }), 400
                elif 'Note' in data:
                    logger.warning(f"Alpha Vantage note: {data['Note']}")
                    return jsonify({
                        'status': 'warning',
                        'message': data['Note']
                    }), 200
                else:
                    return jsonify({
                        'status': 'success',
                        'data': data
                    })
            else:
                logger.error(f"HTTP Error: {response.status_code}")
                return jsonify({
                    'status': 'error',
                    'message': f"HTTP Error: {response.status_code}",
                    'response': response.text
                }), response.status_code
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# Register blueprints
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

if __name__ == '__main__':
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True) 