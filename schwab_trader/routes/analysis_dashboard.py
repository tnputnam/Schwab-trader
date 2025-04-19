from flask import Blueprint, render_template, jsonify, request, current_app
from datetime import datetime, timedelta
import pandas as pd
from schwab_trader.services.data_manager import DataManager
from schwab_trader.services.schwab_market import SchwabMarketAPI
from schwab_trader.utils.logger import setup_logger

analysis_dashboard_bp = Blueprint('analysis_dashboard', __name__, url_prefix='/analysis')
logger = setup_logger('analysis_dashboard')

@analysis_dashboard_bp.route('/')
def index():
    """Render the analysis dashboard."""
    return render_template('analysis_dashboard.html')

@analysis_dashboard_bp.route('/api/market-status')
def get_market_status():
    """Get current market status from Schwab API."""
    try:
        schwab_api = SchwabMarketAPI()
        status = schwab_api.get_market_status()
        return jsonify({
            'status': 'success',
            'data': status
        })
    except Exception as e:
        logger.error(f"Error getting market status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@analysis_dashboard_bp.route('/api/market-data')
def get_market_data():
    """Get market data for analysis."""
    try:
        symbol = request.args.get('symbol', 'AAPL')
        timeframe = request.args.get('timeframe', '1d')
        data_type = request.args.get('type', 'price')

        # Convert timeframe to dates
        end_date = datetime.now()
        if timeframe == '1d':
            start_date = end_date - timedelta(days=1)
        elif timeframe == '1w':
            start_date = end_date - timedelta(weeks=1)
        elif timeframe == '1m':
            start_date = end_date - timedelta(days=30)
        elif timeframe == '3m':
            start_date = end_date - timedelta(days=90)
        elif timeframe == '1y':
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)  # Default to 1 month

        # Get data using DataManager
        data_manager = DataManager()
        data = data_manager.get_historical_data(
            symbol,
            start_date,
            end_date,
            source='auto'
        )

        if data is None or data.empty:
            return jsonify({
                'status': 'error',
                'message': f'No data available for {symbol}'
            }), 404

        # Format response based on data type
        if data_type == 'price':
            response_data = {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'prices': data['close'].tolist(),
                'volumes': data['volume'].tolist()
            }
        elif data_type == 'technical':
            # Calculate technical indicators
            data['SMA_20'] = data['close'].rolling(window=20).mean()
            data['SMA_50'] = data['close'].rolling(window=50).mean()
            data['RSI'] = calculate_rsi(data['close'])
            
            response_data = {
                'dates': data.index.strftime('%Y-%m-%d').tolist(),
                'sma_20': data['SMA_20'].tolist(),
                'sma_50': data['SMA_50'].tolist(),
                'rsi': data['RSI'].tolist()
            }
        else:
            response_data = data.to_dict(orient='records')

        return jsonify({
            'status': 'success',
            'data': response_data,
            'metadata': {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d')
            }
        })

    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@analysis_dashboard_bp.route('/api/verify-auth')
def verify_auth():
    """Verify Schwab API authentication."""
    try:
        schwab_api = SchwabMarketAPI()
        # Try to get a simple quote to verify authentication
        quote = schwab_api.get_quote('AAPL')
        return jsonify({
            'status': 'success',
            'message': 'Authentication successful',
            'data': {
                'timestamp': datetime.now().isoformat(),
                'quote': quote
            }
        })
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 401

def calculate_rsi(prices, periods=14):
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)) 