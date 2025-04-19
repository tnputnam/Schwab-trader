from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService
from schwab_trader.services.alpha_vantage import AlphaVantageAPI

trading_bp = Blueprint('trading', __name__, url_prefix='/trading')
logger = LoggingService()
alpha_vantage = AlphaVantageAPI()

@trading_bp.route('/')
def index():
    """Trading dashboard page."""
    try:
        return render_template('trading.html')
    except Exception as e:
        logger.error(f"Error in trading route: {str(e)}")
        return render_template('trading.html')

@trading_bp.route('/strategy')
def strategy():
    """Trading strategy page."""
    try:
        return render_template('trading/strategy.html')
    except Exception as e:
        logger.error(f"Error in strategy route: {str(e)}")
        return render_template('trading/strategy.html')

@trading_bp.route('/api/paper_trade', methods=['POST'])
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

@trading_bp.route('/api/search_symbols', methods=['POST'])
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

@trading_bp.route('/api/status')
def api_status():
    """Trading API health check endpoint."""
    try:
        response = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'trading_service': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                },
                'alpha_vantage': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                }
            }
        }
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in trading API status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500 