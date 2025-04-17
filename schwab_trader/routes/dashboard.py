from flask import Blueprint, render_template, jsonify
import yfinance as yf
from datetime import datetime, timedelta
import logging

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Configure logging
logger = logging.getLogger('dashboard_routes')
handler = logging.FileHandler('logs/dashboard_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/')
def index():
    """Display the main dashboard."""
    return render_template('index.html')

@bp.route('/tesla_trading')
def tesla_trading():
    """Display the Tesla trading view."""
    return render_template('tesla_trading.html')

@bp.route('/auto_trading')
def auto_trading():
    """Display the auto trading view."""
    return render_template('auto_trading.html')

@bp.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis view."""
    return render_template('volume_analysis.html')

@bp.route('/api/market_data')
def market_data():
    """Get market data for the dashboard."""
    try:
        # Get major indices
        sp500 = yf.Ticker("^GSPC")
        nasdaq = yf.Ticker("^IXIC")
        dow = yf.Ticker("^DJI")
        vix = yf.Ticker("^VIX")

        # Get historical data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)

        sp500_data = sp500.history(start=start_date, end=end_date)
        nasdaq_data = nasdaq.history(start=start_date, end=end_date)
        dow_data = dow.history(start=start_date, end=end_date)
        vix_data = vix.history(start=start_date, end=end_date)

        # Calculate percentage changes
        sp500_change = ((sp500_data['Close'][-1] - sp500_data['Open'][0]) / sp500_data['Open'][0]) * 100
        nasdaq_change = ((nasdaq_data['Close'][-1] - nasdaq_data['Open'][0]) / nasdaq_data['Open'][0]) * 100
        dow_change = ((dow_data['Close'][-1] - dow_data['Open'][0]) / dow_data['Open'][0]) * 100
        vix_value = vix_data['Close'][-1]

        # Get portfolio data (mock for now)
        total_portfolio = 100000.00
        today_pl = 1500.00
        active_positions = 5

        # Get best and worst performers (mock for now)
        best_performer = "AAPL (+2.5%)"
        worst_performer = "TSLA (-1.8%)"
        total_trades = 12

        return jsonify({
            'sp500': sp500_change,
            'nasdaq': nasdaq_change,
            'dow': dow_change,
            'vix': vix_value,
            'totalPortfolio': total_portfolio,
            'todayPL': today_pl,
            'activePositions': active_positions,
            'bestPerformer': best_performer,
            'worstPerformer': worst_performer,
            'totalTrades': total_trades
        })

    except Exception as e:
        logger.error(f"Error fetching market data: {str(e)}")
        return jsonify({'error': 'Failed to fetch market data'}), 500 