from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import requests
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
from schwab_trader.utils.schwab_oauth import SchwabOAuth
from types import SimpleNamespace
from schwab_trader.services.schwab_api import SchwabAPI

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Configure logging
logger = logging.getLogger('dashboard_routes')
handler = logging.FileHandler('logs/dashboard_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize Alpha Vantage API
alpha_vantage = AlphaVantageAPI()

@bp.route('/dashboard')
def index():
    """Dashboard page."""
    try:
        if 'schwab_token' not in session:
            return redirect(url_for('root.login'))
        return render_template('dashboard.html')
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return redirect(url_for('root.login'))

@bp.route('/portfolio')
def portfolio():
    """Portfolio page."""
    try:
        if 'schwab_token' not in session:
            return redirect(url_for('root.login'))
        return render_template('portfolio.html')
    except Exception as e:
        logger.error(f"Error in portfolio route: {str(e)}")
        return redirect(url_for('root.login'))

@bp.route('/trading')
def trading():
    """Display the trading dashboard."""
    if 'schwab_token' not in session:
        return redirect(url_for('auth.schwab_auth'))
    return render_template('trading_dashboard.html')

@bp.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis dashboard."""
    return render_template('tesla_dashboard.html')

@bp.route('/api/paper_trade', methods=['POST'])
def paper_trade():
    """Handle paper trading requests."""
    try:
        if 'schwab_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Process paper trade request
        # Implementation details here
        
        return jsonify({'message': 'Paper trade executed successfully'})
    except Exception as e:
        logger.error(f"Error in paper_trade route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/search_symbols', methods=['POST'])
def search_symbols():
    """Search for stock symbols."""
    try:
        if 'schwab_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No search query provided'}), 400
            
        # Search symbols using AlphaVantage
        results = alpha_vantage.search_symbols(data['query'])
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error in search_symbols route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage():
    """Test Alpha Vantage API connection."""
    try:
        symbol = request.json.get('symbol', 'AAPL')
        response = alpha_vantage.get_quote(symbol)
        
        if 'Note' in response:
            return jsonify({
                'status': 'warning',
                'message': response['Note']
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'data': response
            })
    except Exception as e:
        logger.error(f"Error testing Alpha Vantage: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 