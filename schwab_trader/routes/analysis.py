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

def get_alpha_vantage():
    """Get Alpha Vantage API instance or None if not configured."""
    try:
        return AlphaVantageAPI()
    except ValueError as e:
        logger.warning(f"Alpha Vantage API not configured: {str(e)}")
        return None

@bp.route('/news')
def news():
    """News analysis page."""
    try:
        alpha_vantage = get_alpha_vantage()
        return render_template('analysis_dashboard.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in news route: {str(e)}")
        flash(f"Error loading news page: {str(e)}", "error")
        return render_template('analysis_dashboard.html', alpha_vantage_available=False)

@bp.route('/trading')
def trading():
    """Trading analysis page."""
    try:
        alpha_vantage = get_alpha_vantage()
        return render_template('trading_dashboard.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in trading route: {str(e)}")
        flash(f"Error loading trading page: {str(e)}", "error")
        return render_template('trading_dashboard.html', alpha_vantage_available=False)

@bp.route('/compare')
def compare():
    """Stock comparison page."""
    try:
        alpha_vantage = get_alpha_vantage()
        return render_template('compare.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in compare route: {str(e)}")
        flash(f"Error loading comparison page: {str(e)}", "error")
        return render_template('compare.html', alpha_vantage_available=False)

@bp.route('/volume_analysis')
def volume_analysis():
    """Volume analysis page."""
    try:
        alpha_vantage = get_alpha_vantage()
        if not alpha_vantage:
            return render_template('tesla_dashboard.html', 
                                alpha_vantage_available=False,
                                error="Alpha Vantage API not configured")
        
        # Define stocks to analyze
        stocks = ['TSLA', 'NVDA', 'AAPL']
        stock_data = {}
        
        for symbol in stocks:
            try:
                # Get daily data with full output size for 12 months
                data = alpha_vantage.get_daily_data(symbol, outputsize="full")
                if "Time Series (Daily)" in data:
                    daily_data = data["Time Series (Daily)"]
                    # Convert to list of daily records
                    stock_data[symbol] = [
                        {
                            'date': date,
                            'open': float(day_data['1. open']),
                            'high': float(day_data['2. high']),
                            'low': float(day_data['3. low']),
                            'close': float(day_data['4. close']),
                            'volume': int(day_data['5. volume'])
                        }
                        for date, day_data in daily_data.items()
                    ]
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                stock_data[symbol] = []
        
        return render_template('tesla_dashboard.html', 
                            alpha_vantage_available=True,
                            stock_data=stock_data)
    except Exception as e:
        logger.error(f"Error in volume_analysis route: {str(e)}")
        flash(f"Error loading volume analysis page: {str(e)}", "error")
        return render_template('tesla_dashboard.html', 
                            alpha_vantage_available=False,
                            error=str(e))

@bp.route('/api/volume_analysis', methods=['POST'])
def api_volume_analysis():
    """API endpoint for volume analysis."""
    try:
        alpha_vantage = get_alpha_vantage()
        if not alpha_vantage:
            return jsonify({'error': 'Alpha Vantage API not configured'}), 400
            
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'No symbol provided'}), 400
            
        symbol = data['symbol']
        result = alpha_vantage.get_daily_data(symbol, outputsize="full")
        return jsonify({'result': result})
    except Exception as e:
        logger.error(f"Error in volume_analysis API: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage():
    """Test Alpha Vantage API connection."""
    try:
        alpha_vantage = get_alpha_vantage()
        if not alpha_vantage:
            return jsonify({'error': 'Alpha Vantage API is not configured. Please set ALPHA_VANTAGE_API_KEY environment variable.'}), 400
            
        data = request.get_json()
        if not data or 'symbol' not in data:
            return jsonify({'error': 'No symbol provided'}), 400
            
        result = alpha_vantage.get_quote(data['symbol'])
        return jsonify({'result': result})
    except Exception as e:
        logger.error(f"Error in test_alpha_vantage route: {str(e)}")
        return jsonify({'error': str(e)}), 500 