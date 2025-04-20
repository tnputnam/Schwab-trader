from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash, Response
from flask_login import login_required
import logging
from datetime import datetime, timedelta
from schwab_trader.services.schwab_api import SchwabAPI
import statistics
import os
from schwab_trader.services.volume_analysis import VolumeAnalysisService
from schwab_trader.services.logging_service import LoggingService
import pandas as pd
from schwab_trader.services.strategy_tester import StrategyTester
from schwab_trader.services.schwab_market import SchwabMarketAPI
import json
import time

analysis_bp = Blueprint('analysis', __name__, url_prefix='/analysis')

# Configure logging
logger = LoggingService('analysis').logger

# Initialize services with error handling
try:
    volume_analysis = VolumeAnalysisService()
    strategy_tester = StrategyTester()
    schwab_market = SchwabMarketAPI()
    services_initialized = True
except Exception as e:
    logger.error(f"Error initializing services: {str(e)}")
    services_initialized = False
    volume_analysis = None
    strategy_tester = None
    schwab_market = None

@analysis_bp.route('/')
@login_required
def index():
    """Root analysis page - redirects to the analysis dashboard."""
    return redirect(url_for('analysis.dashboard'))

@analysis_bp.route('/dashboard')
@login_required
def dashboard():
    """Render the analysis dashboard."""
    try:
        # Initialize market status and default data
        market_status = None
        default_symbols = ['AAPL', 'MSFT', 'GOOGL']
        stock_data = {}
        error_messages = []
        
        # Check if services are initialized
        if not services_initialized:
            flash("Some market analysis services are unavailable. Limited functionality may be available.", "warning")
        
        # Try to get market status if service is available
        if schwab_market:
            try:
                market_status = schwab_market.get_market_status()
            except Exception as e:
                logger.error(f"Error getting market status: {str(e)}")
                error_messages.append("Unable to fetch market status")
        
        # Get basic stock data for default symbols
        for symbol in default_symbols:
            try:
                if schwab_market:
                    data = schwab_market.get_latest_data(symbol)
                    if data:
                        stock_data[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                error_messages.append(f"Unable to fetch data for {symbol}")
        
        # Get volume analysis if service is available
        volume_alerts = []
        if volume_analysis:
            try:
                for symbol in stock_data:
                    if symbol in stock_data:
                        alerts = volume_analysis.get_volume_alerts(symbol)
                        volume_alerts.extend(alerts)
            except Exception as e:
                logger.error(f"Error getting volume alerts: {str(e)}")
                error_messages.append("Unable to fetch volume analysis")
        
        return render_template(
            'analysis_dashboard.html',
            market_status=market_status,
            stock_data=stock_data,
            volume_alerts=volume_alerts,
            error_messages=error_messages,
            services_available=services_initialized
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        flash("An error occurred while loading the dashboard. Please try again later.", "error")
        return render_template(
            'analysis_dashboard.html',
            market_status=None,
            stock_data={},
            volume_alerts=[],
            error_messages=[str(e)],
            services_available=False
        )

@analysis_bp.route('/dashboard/api/market-status')
@login_required
def get_market_status():
    """Get current market status from Schwab API."""
    try:
        status = schwab_market.get_market_status()
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

@analysis_bp.route('/dashboard/api/market-data')
@login_required
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
        from schwab_trader.services.data_manager import DataManager
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

@analysis_bp.route('/dashboard/stream-data')
def stream_data():
    """Stream real-time market data."""
    def generate():
        try:
            while True:
                # Get latest market data
                data = schwab_market.get_latest_data()
                yield f"data: {json.dumps(data)}\n\n"
                time.sleep(1)  # Adjust frequency as needed
        except Exception as e:
            logger.error(f"Error in data stream: {str(e)}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')

def get_alpha_vantage():
    """Get Alpha Vantage API instance or None if not configured."""
    try:
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        logger.info(f"Checking Alpha Vantage API key...")
        if not api_key:
            logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        logger.info(f"API key found: {api_key[:4]}...{api_key[-4:]}")
        logger.info(f"API key length: {len(api_key)}")
        logger.info(f"API key type: {type(api_key)}")
        return AlphaVantageAPI()
    except ValueError as e:
        logger.error(f"Alpha Vantage API configuration error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in get_alpha_vantage: {str(e)}", exc_info=True)
        return None

def simulate_volume_trading(data, baseline_period=252, initial_budget=2000):
    """Simulate trading based on volume signals with a fixed budget."""
    if len(data) < baseline_period:
        logger.warning(f"Not enough data points. Have {len(data)}, need {baseline_period}")
        return None
        
    # Calculate baseline volume (average over the baseline period)
    baseline_volume = statistics.mean([d['volume'] for d in data[:baseline_period]])
    logger.info(f"Baseline volume: {baseline_volume:,.0f}")
    logger.info(f"First date: {data[0]['date']}, Last date: {data[-1]['date']}")
    
    trades = []
    position = None
    weekly_trades = 0
    current_week = None
    available_budget = initial_budget
    milestones = []
    last_milestone_budget = initial_budget
    
    for i, day in enumerate(data):
        # Check if we're in a new week
        date = datetime.strptime(day['date'], '%Y-%m-%d')
        week = date.isocalendar()[1]
        if week != current_week:
            current_week = week
            weekly_trades = 0
            logger.info(f"New week {week}, resetting trade count")
            
        # Skip if we've reached the weekly trade limit
        if weekly_trades >= 5:
            continue
            
        volume = day['volume']
        price = day['close']
        
        # Log volume comparison for debugging
        volume_ratio = volume / baseline_volume
        logger.debug(f"Date: {day['date']}, Volume: {volume:,.0f}, Ratio: {volume_ratio:.2f}x baseline")
        
        # Buy signal: volume 10% above baseline
        if not position and volume > baseline_volume * 1.10 and available_budget >= price:
            # Calculate position size (use 50% of available budget)
            position_size = min(available_budget * 0.5, available_budget)
            shares = int(position_size / price)
            
            if shares > 0:  # Only execute if we can buy at least 1 share
                position = {
                    'type': 'buy',
                    'date': day['date'],
                    'price': price,
                    'volume': volume,
                    'shares': shares,
                    'cost': shares * price
                }
                available_budget -= position['cost']
                weekly_trades += 1
                trades.append(position)
                logger.info(f"Buy signal: {day['date']} - Price: ${price:.2f}, Volume: {volume:,.0f} ({(volume_ratio-1)*100:.1f}% above baseline)")
            
        # Sell signal: volume below 10% of baseline
        elif position and volume < baseline_volume * 0.10:
            trade_value = position['shares'] * price
            profit = ((price - position['price']) / position['price']) * 100
            profit_amount = trade_value - position['cost']
            
            trade = {
                'type': 'sell',
                'date': day['date'],
                'price': price,
                'volume': volume,
                'shares': position['shares'],
                'profit': profit,
                'profit_amount': profit_amount,
                'trade_value': trade_value
            }
            
            available_budget += trade_value
            weekly_trades += 1
            trades.append(trade)
            position = None
            logger.info(f"Sell signal: {day['date']} - Price: ${price:.2f}, Volume: {volume:,.0f} ({(volume_ratio-1)*100:.1f}% below baseline), Profit: {profit:.1f}%")
            
            # Check for $500 milestone
            budget_change = available_budget - last_milestone_budget
            if abs(budget_change) >= 500:
                milestone = {
                    'date': day['date'],
                    'type': 'gain' if budget_change > 0 else 'loss',
                    'amount': budget_change,
                    'total': available_budget,
                    'cause': f"Trade profit: {profit:.1f}%"
                }
                milestones.append(milestone)
                last_milestone_budget = available_budget
                logger.info(f"Milestone reached: {milestone['type']} of ${milestone['amount']:.2f}")
    
    # Calculate final metrics
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t['type'] == 'sell' and t['profit'] > 0])
    total_profit = ((available_budget - initial_budget) / initial_budget) * 100
    
    logger.info(f"Simulation complete: {total_trades} trades, {winning_trades} winning trades, {total_profit:.1f}% total profit")
    logger.info(f"Trade dates: {[t['date'] for t in trades]}")
    
    return {
        'trades': trades,
        'milestones': milestones,
        'initial_budget': initial_budget,
        'final_budget': available_budget,
        'total_profit': total_profit,
        'total_profit_amount': available_budget - initial_budget,
        'total_trades': total_trades,
        'winning_trades': winning_trades
    }

@analysis_bp.route('/news')
def news():
    """News analysis page."""
    try:
        alpha_vantage = get_alpha_vantage()
        schwab_api = SchwabAPI()  # Initialize inside route
        return render_template('analysis.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in news route: {str(e)}")
        flash(f"Error loading news page: {str(e)}", "error")
        return render_template('analysis.html', alpha_vantage_available=False)

@analysis_bp.route('/trading')
def trading():
    """Trading analysis page."""
    try:
        alpha_vantage = get_alpha_vantage()
        schwab_api = SchwabAPI()  # Initialize inside route
        return render_template('trading.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in trading route: {str(e)}")
        flash(f"Error loading trading page: {str(e)}", "error")
        return render_template('trading.html', alpha_vantage_available=False)

@analysis_bp.route('/compare')
def compare():
    """Stock comparison page."""
    try:
        alpha_vantage = get_alpha_vantage()
        schwab_api = SchwabAPI()  # Initialize inside route
        return render_template('analysis/compare.html', alpha_vantage_available=alpha_vantage is not None)
    except Exception as e:
        logger.error(f"Error in compare route: {str(e)}")
        flash(f"Error loading comparison page: {str(e)}", "error")
        return render_template('analysis/compare.html', alpha_vantage_available=False)

@analysis_bp.route('/volume-analysis')
def volume_analysis():
    """Render the volume analysis page with data for multiple stocks."""
    try:
        # Get timeframe from request or default to 1 year
        timeframe = request.args.get('timeframe', '1y')
        timeframe_map = {
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825
        }
        days = timeframe_map.get(timeframe, 365)
        
        # Get volume type from request
        volume_type = request.args.get('volume_type', 'raw')
        
        # List of stocks to analyze
        symbols = ['TSLA', 'NVDA', 'AAPL']
        stock_data = {}
        volume_alerts = []
        api_errors = []
        
        for symbol in symbols:
            try:
                # Fetch historical data
                logger.log('INFO', f"Fetching historical data for {symbol}", {
                    'symbol': symbol,
                    'days': days,
                    'volume_type': volume_type
                })
                
                historical_data = schwab_api.get_historical_prices(symbol, days=days)
                if not historical_data:
                    error_msg = f"No data available for {symbol}"
                    logger.log('WARNING', error_msg, {'symbol': symbol})
                    api_errors.append(error_msg)
                    continue
                
                # Extract volumes and process based on type
                volumes = [float(day['volume']) for day in historical_data]
                
                if volume_type == 'relative':
                    # Calculate relative volume (current volume / average volume)
                    avg_volume = sum(volumes) / len(volumes)
                    volumes = [v / avg_volume for v in volumes]
                elif volume_type == 'sma':
                    # Calculate 20-day SMA
                    sma = pd.Series(volumes).rolling(window=20).mean()
                    volumes = sma.tolist()
                
                # Update volume data and get analysis
                analysis = volume_analysis.update_volume_data(symbol, volumes[-1])
                
                # Get volume alerts
                alerts = volume_analysis.get_volume_alerts(symbol)
                volume_alerts.extend(alerts)
                
                # Prepare data for template
                stock_data[symbol] = {
                    'historical_data': historical_data,
                    'analysis': analysis,
                    'alerts': alerts,
                    'volumes': volumes
                }
                
                logger.log('INFO', f"Completed analysis for {symbol}", {
                    'symbol': symbol,
                    'data_points': len(historical_data),
                    'alerts_count': len(alerts)
                })
                
            except Exception as e:
                error_msg = f"Error processing {symbol}: {str(e)}"
                logger.log('ERROR', error_msg, {
                    'symbol': symbol,
                    'error': str(e)
                })
                api_errors.append(error_msg)
                continue
        
        # Get log statistics
        log_stats = logger.get_log_stats()
        
        return render_template(
            'analysis_dashboard.html',
            stock_data=stock_data,
            volume_alerts=volume_alerts,
            api_errors=api_errors,
            timeframe=timeframe,
            volume_type=volume_type,
            log_stats=log_stats
        )
        
    except Exception as e:
        logger.log('ERROR', "Error in volume analysis route", {
            'error': str(e)
        })
        return render_template(
            'analysis_dashboard.html',
            stock_data={},
            volume_alerts=[],
            api_errors=[f"System error: {str(e)}"],
            timeframe='1y',
            volume_type='raw',
            log_stats={'total': 0, 'by_level': {}}
        )

@analysis_bp.route('/api/volume-analysis/<symbol>')
def api_volume_analysis(symbol):
    """API endpoint for volume analysis."""
    try:
        # Get timeframe from request or default to 1 year
        timeframe = request.args.get('timeframe', '1y')
        timeframe_map = {
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365,
            '2y': 730,
            '5y': 1825
        }
        days = timeframe_map.get(timeframe, 365)
        
        logger.log('INFO', f"API request for {symbol} volume analysis", {
            'symbol': symbol,
            'timeframe': timeframe
        })
        
        # Fetch historical data
        historical_data = schwab_api.get_historical_prices(symbol, days=days)
        if not historical_data:
            error_msg = f"No data available for {symbol}"
            logger.log('WARNING', error_msg, {'symbol': symbol})
            return jsonify({'error': error_msg}), 404
        
        # Extract volumes
        volumes = [float(day['volume']) for day in historical_data]
        
        # Update volume data and get analysis
        analysis = volume_analysis.update_volume_data(symbol, volumes[-1])
        
        # Get volume alerts
        alerts = volume_analysis.get_volume_alerts(symbol)
        
        response = {
            'symbol': symbol,
            'analysis': analysis,
            'alerts': alerts,
            'historical_data': historical_data
        }
        
        logger.log('INFO', f"Completed API analysis for {symbol}", {
            'symbol': symbol,
            'data_points': len(historical_data),
            'alerts_count': len(alerts)
        })
        
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Error in volume analysis API: {str(e)}"
        logger.log('ERROR', error_msg, {
            'symbol': symbol,
            'error': str(e)
        })
        return jsonify({'error': error_msg}), 500

@analysis_bp.route('/api/test_alpha_vantage', methods=['POST'])
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

@analysis_bp.route('/test-strategy')
def test_strategy():
    """Test a trading strategy on historical data."""
    try:
        # Get parameters from request
        symbol = request.args.get('symbol', 'TSLA')
        period = request.args.get('period', '1m')
        strategy_type = request.args.get('strategy', 'volume')
        
        # Calculate date range
        end_date = datetime.now()
        if period == '1m':
            start_date = end_date - timedelta(days=30)
        elif period == '3m':
            start_date = end_date - timedelta(days=90)
        elif period == '6m':
            start_date = end_date - timedelta(days=180)
        else:  # 1y
            start_date = end_date - timedelta(days=365)
        
        # Get strategy function based on type
        if strategy_type == 'volume':
            strategy_func = volume_analysis.analyze_volume_pattern
        elif strategy_type == 'technical':
            strategy_func = strategy_tester.calculate_indicators
        else:  # combined
            def combined_strategy(data, timestamp):
                volume_signal = volume_analysis.analyze_volume_pattern(data, timestamp)
                technical_signal = strategy_tester.calculate_indicators(data)
                return {
                    'signal': 'BUY' if volume_signal['signal'] == 'BUY' and technical_signal['signal'] == 'BUY' else 'SELL',
                    'confidence': (volume_signal['confidence'] + technical_signal['confidence']) / 2
                }
            strategy_func = combined_strategy
        
        # Run strategy test
        results = strategy_tester.run_strategy(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            strategy_func=strategy_func
        )
        
        # Calculate performance metrics
        total_trades = len(results['trades'])
        winning_trades = sum(1 for trade in results['trades'] if trade.get('profit', 0) > 0)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        avg_return = sum(trade.get('profit', 0) for trade in results['trades']) / total_trades if total_trades > 0 else 0
        max_drawdown = min(results['daily_returns']) if results['daily_returns'] else 0
        
        # Prepare response
        response = {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'max_drawdown': max_drawdown,
            'performance': {
                'labels': [date.strftime('%Y-%m-%d') for date in results['daily_returns'].index],
                'values': results['portfolio_value']
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error testing strategy: {str(e)}")
        return jsonify({'error': str(e)}), 500

def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs)) 