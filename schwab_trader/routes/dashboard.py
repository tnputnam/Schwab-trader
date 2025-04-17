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
    """Render the main dashboard page."""
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
    logger.info("Accessing strategy dashboard")
    if 'access_token' not in session:
        return redirect(url_for('auth.login'))
    return render_template('strategy_dashboard.html')

@bp.route('/api/market_data')
def get_market_data():
    """Get market data for the dashboard."""
    try:
        # Get market status
        market_status = alpha_vantage.get_market_status()
        
        # Get top gainers and losers
        movers = alpha_vantage.get_top_gainers_losers()
        
        # Get major indices
        indices = {
            'SPY': alpha_vantage.get_global_quote('SPY'),
            'QQQ': alpha_vantage.get_global_quote('QQQ'),
            'DIA': alpha_vantage.get_global_quote('DIA'),
            'VIX': alpha_vantage.get_global_quote('^VIX')
        }
        
        return jsonify({
            'status': 'success',
            'market_status': market_status,
            'movers': movers,
            'indices': indices
        })
    except Exception as e:
        logger.error(f"Error getting market data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/stock_data/<symbol>')
def get_stock_data(symbol):
    """Get detailed stock data for a symbol."""
    try:
        # Get quote data
        quote = alpha_vantage.get_global_quote(symbol)
        
        # Get company overview
        overview = alpha_vantage.get_company_overview(symbol)
        
        # Get intraday data
        intraday = alpha_vantage.get_intraday_data(symbol)
        
        return jsonify({
            'status': 'success',
            'quote': quote,
            'overview': overview,
            'intraday': intraday
        })
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

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
        
        try:
            # Get Tesla data from Alpha Vantage
            data = alpha_vantage.get_intraday_data('TSLA', interval='5min')
            
            if 'Time Series (5min)' not in data:
                logger.error(f"Error in Alpha Vantage response: {data}")
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to fetch Tesla stock data. Please try again later.'
                }), 500
            
            time_series = data['Time Series (5min)']
            
            # Convert time series to list for easier processing
            volumes = []
            prices = []
            timestamps = sorted(time_series.keys(), reverse=True)
            
            # Get last 100 data points (about 8 hours of 5-min data)
            for timestamp in timestamps[:100]:
                entry = time_series[timestamp]
                volumes.append(float(entry['5. volume']))
                prices.append(float(entry['4. close']))
            
            if not volumes or not prices:
                return jsonify({
                    'status': 'error',
                    'message': 'No data available for Tesla stock'
                }), 404
            
            # Calculate volume metrics
            current_volume = volumes[0]  # Most recent volume
            avg_volume = sum(volumes) / len(volumes)
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Calculate price metrics
            current_price = prices[0]  # Most recent price
            prev_price = prices[-1]  # Oldest price in our window
            price_change = ((current_price - prev_price) / prev_price) * 100
            
            # Check for volume signals
            signal = None
            if volume_ratio > 1.5:  # 50% above average volume
                signal = {
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'type': 'High Volume',
                    'message': f'Volume is {volume_ratio:.2f}x above average'
                }
            
            logger.info("Tesla analysis completed successfully")
            return jsonify({
                'status': 'success',
                'metrics': {
                    'volumeRatio': volume_ratio,
                    'priceChange': price_change
                },
                'signal': signal
            })
            
        except Exception as e:
            logger.error(f"Error fetching Tesla data: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to fetch Tesla stock data. Please try again later.'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in Tesla analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred'
        }), 500

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

@bp.route('/api/search_symbols', methods=['POST'])
def search_symbols():
    """Search for symbols matching the query."""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Query parameter is required'
            }), 400
            
        results = alpha_vantage.search_symbols(query)
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        logger.error(f"Error searching symbols: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 