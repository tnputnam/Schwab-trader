from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
import logging
from datetime import datetime
from schwab_trader.services.alpha_vantage import AlphaVantageAPI

bp = Blueprint('analysis', __name__)

# Configure logging
logger = logging.getLogger('analysis_routes')
handler = logging.FileHandler('logs/analysis_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/news')
def news():
    """News analysis page."""
    try:
        return render_template('analysis_dashboard.html')
    except Exception as e:
        logger.error(f"Error in news route: {str(e)}")
        flash(f"Error loading news page: {str(e)}", "error")
        return render_template('analysis_dashboard.html')

@bp.route('/trading')
def trading():
    """Trading analysis page."""
    try:
        return render_template('trading_dashboard.html')
    except Exception as e:
        logger.error(f"Error in trading route: {str(e)}")
        flash(f"Error loading trading page: {str(e)}", "error")
        return render_template('trading_dashboard.html')

@bp.route('/compare')
def compare():
    """Stock comparison page."""
    try:
        return render_template('compare.html')
    except Exception as e:
        logger.error(f"Error in compare route: {str(e)}")
        flash(f"Error loading comparison page: {str(e)}", "error")
        return render_template('compare.html')

@bp.route('/volume_analysis')
def volume_analysis():
    """Volume analysis page."""
    try:
        return render_template('tesla_dashboard.html')
    except Exception as e:
        logger.error(f"Error in volume_analysis route: {str(e)}")
        flash(f"Error loading volume analysis page: {str(e)}", "error")
        return render_template('tesla_dashboard.html')

@bp.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage():
    """Test Alpha Vantage API connection."""
    try:
        if 'schwab_token' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
            
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'No symbol provided'}), 400
            
        # Test Alpha Vantage API
        alpha_vantage = AlphaVantageAPI()
        result = alpha_vantage.get_quote(data['symbol'])
        
        return jsonify({'result': result})
    except Exception as e:
        logger.error(f"Error in test_alpha_vantage route: {str(e)}")
        return jsonify({'error': str(e)}), 500 