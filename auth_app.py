from flask import Flask, session, redirect, request, jsonify, url_for, render_template, current_app
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
from dotenv import load_dotenv
from schwab_trader.routes.root import root_bp
from schwab_trader.routes.analysis import analysis_bp

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)  # Changed to DEBUG level
logger = logging.getLogger(__name__)

# Debug print environment variables
logger.debug("Environment Variables:")
for key in ['SCHWAB_CLIENT_ID', 'SCHWAB_CLIENT_SECRET', 'SCHWAB_REDIRECT_URI', 
            'SCHWAB_AUTH_URL', 'SCHWAB_TOKEN_URL', 'SCHWAB_SCOPES', 'SCHWAB_API_BASE_URL']:
    value = os.getenv(key)
    logger.debug(f"{key}: {value}")
    if not value:
        logger.error(f"Missing environment variable: {key}")

app = Flask(__name__, 
    template_folder='schwab_trader/templates',
    static_folder='schwab_trader/static'
)
CORS(app)

# Register blueprints
app.register_blueprint(root_bp)
app.register_blueprint(analysis_bp, url_prefix='/analysis')

# Load configuration from environment variables
config = {
    'SECRET_KEY': os.getenv('FLASK_SECRET_KEY', 'dev_key_123'),
    'SCHWAB_CLIENT_ID': os.getenv('SCHWAB_CLIENT_ID'),
    'SCHWAB_CLIENT_SECRET': os.getenv('SCHWAB_CLIENT_SECRET'),
    'SCHWAB_REDIRECT_URI': os.getenv('SCHWAB_REDIRECT_URI'),
    'SCHWAB_AUTH_URL': os.getenv('SCHWAB_AUTH_URL'),
    'SCHWAB_TOKEN_URL': os.getenv('SCHWAB_TOKEN_URL'),
    'SCHWAB_SCOPES': os.getenv('SCHWAB_SCOPES'),
    'SCHWAB_API_BASE_URL': os.getenv('SCHWAB_API_BASE_URL', 'https://api.schwabapi.com/v1')
}

# Update Flask config
app.config.update(config)

# Debug print Flask config after update
logger.debug("\nFlask Configuration:")
for key in ['SCHWAB_CLIENT_ID', 'SCHWAB_CLIENT_SECRET', 'SCHWAB_REDIRECT_URI', 
            'SCHWAB_AUTH_URL', 'SCHWAB_TOKEN_URL', 'SCHWAB_SCOPES', 'SCHWAB_API_BASE_URL']:
    logger.debug(f"{key}: {app.config.get(key)}")

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///schwab_trader.db')
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

def get_schwab_oauth():
    """Get an instance of SchwabOAuth."""
    try:
        schwab = SchwabOAuth()
        logger.debug("SchwabOAuth instance created successfully")
        return schwab
    except Exception as e:
        logger.error(f"Error creating SchwabOAuth instance: {str(e)}")
        raise

# Schwab OAuth routes
@app.route('/auth/schwab')
def schwab_auth():
    """Start the Schwab OAuth flow."""
    try:
        logger.debug("Starting Schwab auth flow")
        schwab = get_schwab_oauth()
        auth_url = schwab.get_authorization_url()
        logger.debug(f"Auth URL: {auth_url}")
        
        # Return the URL instead of redirecting
        return jsonify({
            'status': 'success',
            'auth_url': auth_url
        })
    except Exception as e:
        logger.error(f"Error starting Schwab auth: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/auth/manual')
def manual_auth():
    """Display a page with instructions for manual authorization."""
    return render_template('manual_auth.html')

@app.route('/auth/callback')
def schwab_callback():
    """Handle the OAuth callback from Schwab."""
    try:
        # Validate state parameter
        if 'state' not in request.args:
            logger.error("No state parameter in callback")
            return render_template('error.html', error_message="Missing state parameter in callback")
            
        if 'oauth_state' not in session:
            logger.error("No state stored in session")
            return render_template('error.html', error_message="Missing state in session")
            
        if request.args['state'] != session['oauth_state']:
            logger.error("State mismatch")
            return render_template('error.html', error_message="State mismatch in callback")
            
        # Clear the state from session
        session.pop('oauth_state', None)
        
        # Get token
        schwab = get_schwab_oauth()
        token = schwab.fetch_token(request.url)
        
        if not token:
            logger.error("Failed to get token")
            return render_template('error.html', error_message="Failed to get access token")
            
        # Store the token in the session
        session['schwab_token'] = token
        
        try:
            # Get user's accounts
            accounts = schwab.get_accounts()
            if accounts:
                session['schwab_accounts'] = accounts
                return redirect(url_for('analysis.dashboard'))
            else:
                logger.error("Failed to get accounts")
                return render_template('error.html', error_message="Failed to get account information")
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return render_template('error.html', error_message=f"Error getting account information: {str(e)}")
            
    except Exception as e:
        logger.error(f"Error in Schwab callback: {str(e)}")
        return render_template('error.html', error_message=f"Error during authentication: {str(e)}")

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

@app.route('/login')
def login():
    """Automatically redirect to analysis dashboard"""
    return redirect(url_for('analysis.dashboard'))

@app.route('/analysis')
def analysis():
    """Display the analysis dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('manual_auth'))
    return redirect(url_for('analysis.dashboard'))

@app.route('/trading')
def trading():
    """Display the trading dashboard page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('trading.html')

@app.route('/portfolio')
def portfolio():
    """Display the portfolio page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('portfolio.html')

@app.route('/news')
def news():
    """Display the news page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('news.html')

@app.route('/compare')
def compare():
    """Display the stock comparison page"""
    if 'schwab_token' not in session:
        return redirect(url_for('schwab_auth'))
    return render_template('analysis/compare.html')

@app.route('/api/paper_trade', methods=['POST'])
def paper_trade():
    """Handle paper trading requests"""
    if 'schwab_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    try:
        # Process paper trade request
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search_symbols', methods=['POST'])
def search_symbols():
    """Search for stock symbols"""
    if 'schwab_token' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({'error': 'No search query provided'}), 400
    
    try:
        # Search for symbols
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test_alpha_vantage')
def test_alpha_vantage():
    """Test Alpha Vantage API connection"""
    return render_template('test_alpha_vantage.html')

@app.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage_api():
    """Test Alpha Vantage API connection"""
    data = request.get_json()
    if not data or 'symbol' not in data:
        return jsonify({'error': 'No symbol provided'}), 400
    
    try:
        # Test Alpha Vantage API
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True) 