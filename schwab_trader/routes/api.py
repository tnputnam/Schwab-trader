from flask import Blueprint, jsonify, current_app
from schwab_trader.utils.logger import setup_logger

logger = setup_logger(__name__)
api_bp = Blueprint('api', __name__)

@api_bp.route('/api/status')
def get_api_status():
    """Get the current status of all APIs."""
    try:
        status = {
            'schwab': 'connected' if hasattr(current_app, 'schwab') and current_app.schwab.is_connected() else 'disconnected',
            'alpha_vantage': 'connected' if hasattr(current_app, 'alpha_vantage') and current_app.alpha_vantage.is_connected() else 'disconnected',
            'yfinance': 'connected' if hasattr(current_app, 'yfinance') and current_app.yfinance.is_connected() else 'disconnected'
        }
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting API status: {str(e)}")
        return jsonify({
            'schwab': 'error',
            'alpha_vantage': 'error',
            'yfinance': 'error'
        }), 500

@api_bp.route('/api/schwab/<action>', methods=['POST'])
def toggle_schwab(action):
    """Toggle Schwab API connection."""
    try:
        if action == 'connect':
            if not hasattr(current_app, 'schwab'):
                current_app.schwab = SchwabAPI()
                current_app.schwab.init_app(current_app)
            current_app.schwab.connect()
            return jsonify({'status': 'connected'})
        elif action == 'disconnect':
            if hasattr(current_app, 'schwab'):
                current_app.schwab.disconnect()
            return jsonify({'status': 'disconnected'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Error toggling Schwab API: {str(e)}")
        return jsonify({'status': 'error'}), 500

@api_bp.route('/api/alpha-vantage/<action>', methods=['POST'])
def toggle_alpha_vantage(action):
    """Toggle Alpha Vantage API connection."""
    try:
        if action == 'connect':
            if not hasattr(current_app, 'alpha_vantage'):
                current_app.alpha_vantage = AlphaVantageAPI()
                current_app.alpha_vantage.init_app(current_app)
            current_app.alpha_vantage.connect()
            return jsonify({'status': 'connected'})
        elif action == 'disconnect':
            if hasattr(current_app, 'alpha_vantage'):
                current_app.alpha_vantage.disconnect()
            return jsonify({'status': 'disconnected'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Error toggling Alpha Vantage API: {str(e)}")
        return jsonify({'status': 'error'}), 500

@api_bp.route('/api/yfinance/<action>', methods=['POST'])
def toggle_yfinance(action):
    """Toggle Yahoo Finance API connection."""
    try:
        if action == 'connect':
            if not hasattr(current_app, 'yfinance'):
                current_app.yfinance = YFinanceAPI()
                current_app.yfinance.init_app(current_app)
            current_app.yfinance.connect()
            return jsonify({'status': 'connected'})
        elif action == 'disconnect':
            if hasattr(current_app, 'yfinance'):
                current_app.yfinance.disconnect()
            return jsonify({'status': 'disconnected'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
    except Exception as e:
        logger.error(f"Error toggling Yahoo Finance API: {str(e)}")
        return jsonify({'status': 'error'}), 500 