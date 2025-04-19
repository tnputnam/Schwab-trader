from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import requests
from schwab_trader.services.alpha_vantage import AlphaVantageAPI

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Configure logging
logger = logging.getLogger('dashboard_routes')
handler = logging.FileHandler('logs/dashboard_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize Alpha Vantage API
alpha_vantage = AlphaVantageAPI()

@bp.route('/')
def index():
    """Dashboard page."""
    try:
        return render_template('market_dashboard.html')
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('market_dashboard.html')

@bp.route('/portfolio')
def portfolio():
    """Portfolio page."""
    try:
        return render_template('portfolio.html')
    except Exception as e:
        logger.error(f"Error in portfolio route: {str(e)}")
        return render_template('portfolio.html')

@bp.route('/trading')
def trading():
    """Display the trading dashboard."""
    return render_template('trading_dashboard.html')

@bp.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis dashboard."""
    if 'schwab_token' not in session:
        return redirect(url_for('auth.schwab_auth'))
    return render_template('tesla_dashboard.html')

@bp.route('/api/paper_trade', methods=['POST'])
def paper_trade():
    """Handle paper trading requests."""
    try:
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

@bp.route('/api/status')
def api_status():
    """Mock API health check endpoint."""
    try:
        # Simulate API response with mock data
        mock_response = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'schwab_api': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                },
                'alpha_vantage': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                },
                'yfinance': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                }
            }
        }
        return jsonify(mock_response)
    except Exception as e:
        logger.error(f"Error in mock API status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@bp.route('/api/test_data/<symbol>')
def get_test_data(symbol):
    """Serve test historical data for a symbol."""
    try:
        # For now, we'll use a simple mock data structure
        mock_data = {
            'prices': [
                {'date': '2025-01-01', 'open': 100.0, 'high': 105.0, 'low': 98.0, 'close': 102.0, 'volume': 1000000},
                {'date': '2025-01-02', 'open': 102.0, 'high': 108.0, 'low': 101.0, 'close': 107.0, 'volume': 1200000},
                {'date': '2025-01-03', 'open': 107.0, 'high': 110.0, 'low': 105.0, 'close': 108.0, 'volume': 900000},
                {'date': '2025-01-04', 'open': 108.0, 'high': 112.0, 'low': 106.0, 'close': 110.0, 'volume': 1100000},
                {'date': '2025-01-05', 'open': 110.0, 'high': 115.0, 'low': 109.0, 'close': 114.0, 'volume': 1300000}
            ],
            'trades': [
                {'date': '2025-01-02', 'type': 'buy', 'price': 102.0, 'volume': 1000},
                {'date': '2025-01-04', 'type': 'sell', 'price': 110.0, 'volume': 1000}
            ]
        }
        
        return jsonify({
            'status': 'success',
            'symbol': symbol,
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"Error serving test data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 