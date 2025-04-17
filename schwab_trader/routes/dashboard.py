from flask import Blueprint, render_template, jsonify, request, session
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

@bp.route('/strategy_dashboard')
def strategy_dashboard():
    """Display the strategy dashboard view."""
    return render_template('strategy_dashboard.html')

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

@bp.route('/api/start_volume_analysis', methods=['POST'])
def start_volume_analysis():
    """Start volume analysis for a given symbol and timeframe."""
    try:
        logger.info("Received start volume analysis request")
        data = request.get_json()
        symbol = data.get('symbol', 'TSLA')
        timeframe = data.get('timeframe', '1m')
        
        logger.info(f"Starting volume analysis for {symbol} with timeframe {timeframe}")
        
        # Store analysis parameters in session
        session['volume_analysis'] = {
            'symbol': symbol,
            'timeframe': timeframe,
            'is_running': True
        }
        
        logger.info("Volume analysis started successfully")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error starting volume analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/stop_volume_analysis', methods=['POST'])
def stop_volume_analysis():
    """Stop the running volume analysis."""
    try:
        logger.info("Received stop volume analysis request")
        if 'volume_analysis' in session:
            session['volume_analysis']['is_running'] = False
            logger.info("Volume analysis stopped successfully")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.error(f"Error stopping volume analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/volume_analysis_updates')
def volume_analysis_updates():
    """Get updates for the volume analysis."""
    try:
        logger.info("Received volume analysis updates request")
        if 'volume_analysis' not in session or not session['volume_analysis']['is_running']:
            logger.info("Volume analysis is not running")
            return jsonify({'status': 'stopped'})
            
        symbol = session['volume_analysis']['symbol']
        timeframe = session['volume_analysis']['timeframe']
        
        logger.info(f"Fetching updates for {symbol} with timeframe {timeframe}")
        
        # Get stock data
        stock = yf.Ticker(symbol)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        hist = stock.history(start=start_date, end=end_date, interval=timeframe)
        
        if hist.empty:
            logger.warning(f"No data available for {symbol}")
            return jsonify({'status': 'error', 'message': 'No data available'}), 404
        
        # Calculate metrics
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].mean()
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        volume_ratio = current_volume / avg_volume
        
        # Prepare chart data
        chart_data = {
            'labels': [str(x) for x in hist.index],
            'volumes': hist['Volume'].tolist()
        }
        
        # Check for volume signals
        signal = None
        if volume_ratio > 1.5:  # 50% above average volume
            signal = {
                'time': datetime.now().strftime('%H:%M:%S'),
                'type': 'High Volume',
                'message': f'Volume is {volume_ratio:.2f}x above average'
            }
        
        logger.info(f"Successfully generated updates for {symbol}")
        return jsonify({
            'status': 'success',
            'chartData': chart_data,
            'metrics': {
                'currentVolume': current_volume,
                'volumeChange': volume_change,
                'avgVolume': avg_volume,
                'volumeRatio': volume_ratio
            },
            'signal': signal
        })
    except Exception as e:
        logger.error(f"Error getting volume analysis updates: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500 

@bp.route('/api/run_tesla_analysis', methods=['POST'])
def run_tesla_analysis():
    """Run Tesla volume analysis."""
    try:
        logger.info("Running Tesla volume analysis")
        # Get Tesla data
        tesla = yf.Ticker("TSLA")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        hist = tesla.history(start=start_date, end=end_date)
        
        if hist.empty:
            return jsonify({'status': 'error', 'message': 'No data available'}), 404
        
        # Calculate volume metrics
        current_volume = hist['Volume'].iloc[-1]
        avg_volume = hist['Volume'].mean()
        volume_change = ((current_volume - avg_volume) / avg_volume) * 100
        volume_ratio = current_volume / avg_volume
        
        # Calculate price metrics
        current_price = hist['Close'].iloc[-1]
        price_change = ((current_price - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
        
        return jsonify({
            'status': 'success',
            'metrics': {
                'currentVolume': current_volume,
                'avgVolume': avg_volume,
                'volumeChange': volume_change,
                'volumeRatio': volume_ratio,
                'currentPrice': current_price,
                'priceChange': price_change
            }
        })
    except Exception as e:
        logger.error(f"Error running Tesla analysis: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/run_backtest', methods=['POST'])
def run_backtest():
    """Run backtesting for given symbols and date range."""
    try:
        data = request.get_json()
        symbols = [s.strip() for s in data.get('symbols', '').split(',')]
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        if not symbols or not start_date or not end_date:
            return jsonify({'status': 'error', 'message': 'Missing required parameters'}), 400
        
        results = []
        for symbol in symbols:
            stock = yf.Ticker(symbol)
            hist = stock.history(start=start_date, end=end_date)
            
            if not hist.empty:
                initial_price = hist['Close'].iloc[0]
                final_price = hist['Close'].iloc[-1]
                total_return = ((final_price - initial_price) / initial_price) * 100
                
                results.append({
                    'symbol': symbol,
                    'initialPrice': initial_price,
                    'finalPrice': final_price,
                    'totalReturn': total_return
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500 