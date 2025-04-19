from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import requests
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
import pandas as pd
import numpy as np

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
        # Generate 12 months of mock data for TSLA
        # Create date range for the past 12 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate mock price data with some realistic volatility
        # Start with a realistic TSLA price
        base_price = 180.0
        prices = []
        current_price = base_price
        
        for date in dates:
            # Generate daily price movement
            daily_change = np.random.normal(0, 2.0)  # Average daily change of $2
            current_price += daily_change
            current_price = max(100, min(300, current_price))  # Keep within reasonable range
            
            # Generate volume with some randomness
            base_volume = 100000000  # 100M shares
            volume = int(base_volume * (1 + np.random.normal(0, 0.3)))
            
            # Calculate OHLC
            open_price = current_price
            high_price = current_price * (1 + abs(np.random.normal(0, 0.02)))
            low_price = current_price * (1 - abs(np.random.normal(0, 0.02)))
            close_price = current_price
            
            prices.append({
                'date': date.strftime('%Y-%m-%d'),
                'open': round(open_price, 2),
                'high': round(high_price, 2),
                'low': round(low_price, 2),
                'close': round(close_price, 2),
                'volume': volume
            })
        
        # Generate some mock trades
        trades = []
        for _ in range(10):  # 10 random trades
            trade_date = np.random.choice(dates)
            trade_price = np.random.uniform(min(p['low'] for p in prices), max(p['high'] for p in prices))
            trade_type = np.random.choice(['buy', 'sell'])
            trade_volume = int(np.random.uniform(100, 1000))
            
            trades.append({
                'date': trade_date.strftime('%Y-%m-%d'),
                'type': trade_type,
                'price': round(trade_price, 2),
                'volume': trade_volume
            })
        
        mock_data = {
            'prices': prices,
            'trades': trades
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