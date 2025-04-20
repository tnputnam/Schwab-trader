from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required
from schwab_trader.services.data_service import DataService
from schwab_trader.utils.error_utils import APIError, NetworkError, ValidationError
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)
data_bp = Blueprint('data', __name__, url_prefix='/api/data')

@data_bp.route('/quote/<symbol>', methods=['GET'])
@login_required
def get_quote(symbol):
    """Get real-time stock quote."""
    try:
        data_service = DataService(current_app.config['ALPHA_VANTAGE_API_KEY'])
        quote = data_service.get_stock_quote(symbol)
        return jsonify(quote)
    except (APIError, NetworkError, ValidationError) as e:
        logger.error(f"Error getting quote for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code

@data_bp.route('/intraday/<symbol>', methods=['GET'])
@login_required
def get_intraday_data(symbol):
    """Get intraday stock data."""
    try:
        interval = request.args.get('interval', default='5min')
        data_service = DataService(current_app.config['ALPHA_VANTAGE_API_KEY'])
        data = data_service.get_intraday_data(symbol, interval)
        return jsonify(data)
    except (APIError, NetworkError, ValidationError) as e:
        logger.error(f"Error getting intraday data for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code

@data_bp.route('/daily/<symbol>', methods=['GET'])
@login_required
def get_daily_data(symbol):
    """Get daily stock data."""
    try:
        output_size = request.args.get('output_size', default='compact')
        data_service = DataService(current_app.config['ALPHA_VANTAGE_API_KEY'])
        data = data_service.get_daily_data(symbol, output_size)
        return jsonify(data)
    except (APIError, NetworkError, ValidationError) as e:
        logger.error(f"Error getting daily data for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code

@data_bp.route('/company/<symbol>', methods=['GET'])
@login_required
def get_company_overview(symbol):
    """Get company overview information."""
    try:
        data_service = DataService(current_app.config['ALPHA_VANTAGE_API_KEY'])
        data = data_service.get_company_overview(symbol)
        return jsonify(data)
    except (APIError, NetworkError, ValidationError) as e:
        logger.error(f"Error getting company overview for {symbol}: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code

@data_bp.route('/search', methods=['GET'])
@login_required
def search_symbols():
    """Search for stock symbols."""
    try:
        keywords = request.args.get('q', '')
        if not keywords:
            return jsonify({'error': 'Search query is required'}), 400
            
        data_service = DataService(current_app.config['ALPHA_VANTAGE_API_KEY'])
        results = data_service.search_symbols(keywords)
        return jsonify(results)
    except (APIError, NetworkError, ValidationError) as e:
        logger.error(f"Error searching symbols: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code 