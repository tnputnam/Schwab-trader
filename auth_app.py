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
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    """Display the dashboard page"""
    return render_template('index.html')

@app.route('/portfolio')
def portfolio():
    """Display the portfolio page"""
    try:
        # Create a mock portfolio for now - this should be replaced with actual data from your database
        portfolio = {
            'updated_at': datetime.now(),
            'total_value': 100000.00,
            'cash_value': 25000.00,
            'day_change': 1500.00,
            'day_change_percent': 1.5,
            'total_gain': 10000.00,
            'total_gain_percent': 10.0
        }
        
        # Mock positions data
        positions = [
            {
                'symbol': 'AAPL',
                'description': 'Apple Inc.',
                'quantity': 100,
                'price': 150.00,
                'market_value': 15000.00,
                'day_change_dollar': 300.00,
                'day_change_percent': 2.0,
                'cost_basis': 14000.00,
                'security_type': 'Stock',
                'sector': 'Technology',
                'industry': 'Consumer Electronics',
                'pe_ratio': 25.5,
                'market_cap': 2500000000000.00,
                'dividend_yield': 0.65,
                'eps': 5.89,
                'beta': 1.2,
                'volume': 80000000
            },
            {
                'symbol': 'MSFT',
                'description': 'Microsoft Corporation',
                'quantity': 50,
                'price': 300.00,
                'market_value': 15000.00,
                'day_change_dollar': 150.00,
                'day_change_percent': 1.0,
                'cost_basis': 14500.00,
                'security_type': 'Stock',
                'sector': 'Technology',
                'industry': 'Software',
                'pe_ratio': 30.2,
                'market_cap': 2000000000000.00,
                'dividend_yield': 0.85,
                'eps': 9.65,
                'beta': 0.95,
                'volume': 25000000
            }
        ]
        
        # Calculate sector allocation
        sector_data = {}
        for position in positions:
            sector = position['sector']
            value = position['market_value']
            sector_data[sector] = sector_data.get(sector, 0) + value
        
        sector_labels = list(sector_data.keys())
        sector_values = list(sector_data.values())
        
        # Calculate asset type allocation
        asset_type_data = {}
        for position in positions:
            asset_type = position['security_type']
            value = position['market_value']
            asset_type_data[asset_type] = asset_type_data.get(asset_type, 0) + value
        
        asset_type_labels = list(asset_type_data.keys())
        asset_type_values = list(asset_type_data.values())
        
        return render_template('portfolio.html',
                             portfolio=SimpleNamespace(**portfolio),
                             positions=positions,
                             sector_labels=sector_labels,
                             sector_values=sector_values,
                             asset_type_labels=asset_type_labels,
                             asset_type_values=asset_type_values)
                             
    except Exception as e:
        flash(f'Error loading portfolio: {str(e)}', 'danger')
        return render_template('portfolio.html',
                             portfolio=SimpleNamespace(updated_at=datetime.now(),
                                                     total_value=0.00,
                                                     cash_value=0.00,
                                                     day_change=0.00,
                                                     day_change_percent=0.00,
                                                     total_gain=0.00,
                                                     total_gain_percent=0.00),
                             positions=[],
                             sector_labels=[],
                             sector_values=[],
                             asset_type_labels=[],
                             asset_type_values=[])

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

@app.route('/dashboard/api/paper_trade', methods=['POST'])
def paper_trade():
    """Run paper trading with selected strategy"""
    try:
        if 'access_token' not in session:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401
            
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
        tester.sync_with_schwab(session['access_token'])
        
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

if __name__ == '__main__':
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True) 