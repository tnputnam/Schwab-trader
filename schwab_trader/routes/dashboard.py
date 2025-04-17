from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import requests

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Configure logging
logger = logging.getLogger('dashboard_routes')
handler = logging.FileHandler('logs/dashboard_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class AlphaVantageAPI:
    def __init__(self):
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = 'https://www.alphavantage.co/query'
        
    def get_intraday_data(self, symbol, interval='5min'):
        """Get intraday data for a symbol."""
        params = {
            'function': 'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'interval': interval,
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        response = requests.get(self.base_url, params=params)
        return response.json()

# Initialize Alpha Vantage API
alpha_vantage = AlphaVantageAPI()

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
    logger.info("Accessing strategy dashboard")
    if 'access_token' not in session:
        return redirect(url_for('auth.login'))
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
    """Search for symbols or company names"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip().upper()
        
        if not query:
            return jsonify({
                'status': 'error',
                'message': 'Search query is required'
            }), 400
        
        # Try Alpha Vantage first
        try:
            api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
            if not api_key:
                raise Exception("Alpha Vantage API key not found")
            
            url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'bestMatches' in data:
                    results = []
                    for match in data['bestMatches']:
                        results.append({
                            'symbol': match['1. symbol'],
                            'name': match['2. name'],
                            'type': match['3. type'],
                            'region': match['4. region']
                        })
                    return jsonify({
                        'status': 'success',
                        'results': results
                    })
        except Exception as e:
            logger.warning(f"Alpha Vantage search failed: {str(e)}")
        
        # Fallback to yfinance
        try:
            # Get list of major stocks
            major_stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 'INTC', 'QCOM']
            results = []
            
            for symbol in major_stocks:
                try:
                    stock = yf.Ticker(symbol)
                    info = stock.info
                    name = info.get('longName', '')
                    
                    if query in symbol or query in name.upper():
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'type': info.get('quoteType', ''),
                            'region': info.get('region', '')
                        })
                except:
                    continue
            
            return jsonify({
                'status': 'success',
                'results': results
            })
        except Exception as e:
            logger.error(f"yfinance search failed: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': 'Failed to search symbols'
            }), 500
            
    except Exception as e:
        logger.error(f"Error in symbol search: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 