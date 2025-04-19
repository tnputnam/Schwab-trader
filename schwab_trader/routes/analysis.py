from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
import logging
from datetime import datetime, timedelta
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
import statistics
import os

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
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        logger.info(f"Checking Alpha Vantage API key...")
        if not api_key:
            logger.error("ALPHA_VANTAGE_API_KEY environment variable not set")
            raise ValueError("ALPHA_VANTAGE_API_KEY environment variable not set")
        logger.info(f"API key found: {api_key[:4]}...{api_key[-4:]}")
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
        logger.info("Starting volume analysis...")
        alpha_vantage = get_alpha_vantage()
        if not alpha_vantage:
            logger.error("Alpha Vantage API not configured")
            return render_template('analysis_dashboard.html', 
                                alpha_vantage_available=False,
                                error="Alpha Vantage API not configured",
                                stock_data={},
                                simulation_results={},
                                active_tab='volume')
        
        logger.info("Alpha Vantage API configured successfully")
        # Define stocks to analyze
        stocks = ['TSLA', 'NVDA', 'AAPL']
        stock_data = {}
        simulation_results = {}
        
        for symbol in stocks:
            try:
                logger.info(f"Fetching data for {symbol}...")
                # Get daily data with full output size for 12 months
                data = alpha_vantage.get_daily_data(symbol, outputsize="full")
                logger.info(f"Raw API response for {symbol}: {data.keys()}")
                
                if "Time Series (Daily)" in data:
                    daily_data = data["Time Series (Daily)"]
                    logger.info(f"Found {len(daily_data)} days of data for {symbol}")
                    
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
                    # Sort by date
                    stock_data[symbol].sort(key=lambda x: x['date'])
                    logger.info(f"Processed {len(stock_data[symbol])} days of data for {symbol}")
                    logger.info(f"Date range for {symbol}: {stock_data[symbol][0]['date']} to {stock_data[symbol][-1]['date']}")
                    
                    # Run simulation
                    simulation_results[symbol] = simulate_volume_trading(stock_data[symbol])
                    if simulation_results[symbol]:
                        logger.info(f"Simulation results for {symbol}: {len(simulation_results[symbol]['trades'])} trades")
                else:
                    logger.error(f"No time series data found for {symbol}. API response: {data}")
                    stock_data[symbol] = []
                    simulation_results[symbol] = None
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}", exc_info=True)
                stock_data[symbol] = []
                simulation_results[symbol] = None
        
        logger.info("Rendering template with data...")
        return render_template('analysis_dashboard.html', 
                            alpha_vantage_available=True,
                            stock_data=stock_data,
                            simulation_results=simulation_results,
                            active_tab='volume')
    except Exception as e:
        logger.error(f"Error in volume_analysis route: {str(e)}", exc_info=True)
        flash(f"Error loading volume analysis page: {str(e)}", "error")
        return render_template('analysis_dashboard.html', 
                            alpha_vantage_available=False,
                            error=str(e),
                            stock_data={},
                            simulation_results={},
                            active_tab='volume')

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