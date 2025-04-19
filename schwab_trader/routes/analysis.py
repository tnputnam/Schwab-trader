from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, flash
import logging
from datetime import datetime, timedelta
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
import statistics

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

def simulate_volume_trading(data, baseline_period=252, initial_budget=2000):
    """Simulate trading based on volume signals with a fixed budget."""
    if len(data) < baseline_period:
        return None
        
    # Calculate baseline volume (average over the baseline period)
    baseline_volume = statistics.mean([d['volume'] for d in data[:baseline_period]])
    
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
            
        # Skip if we've reached the weekly trade limit
        if weekly_trades >= 5:
            continue
            
        volume = day['volume']
        price = day['close']
        
        # Buy signal: volume 15% above baseline
        if not position and volume > baseline_volume * 1.15 and available_budget >= price:
            # Calculate position size (use 20% of available budget)
            position_size = min(available_budget * 0.2, available_budget)
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
            
        # Sell signal: volume below 5% of baseline
        elif position and volume < baseline_volume * 0.05:
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
            
            # Check for $500 milestone
            budget_change = available_budget - last_milestone_budget
            if abs(budget_change) >= 500:
                milestone = {
                    'date': day['date'],
                    'type': 'gain' if budget_change > 0 else 'loss',
                    'amount': abs(budget_change),
                    'total': available_budget,
                    'cause': f"{'Gain' if budget_change > 0 else 'Loss'} of ${abs(profit_amount):.2f} from {position['shares']} shares of {position['price']:.2f} → {price:.2f}"
                }
                milestones.append(milestone)
                last_milestone_budget = available_budget
            
            position = None
            
    # Calculate final metrics
    total_profit = sum([t['profit_amount'] for t in trades if t['type'] == 'sell'])
    total_profit_percentage = (total_profit / initial_budget) * 100
    winning_trades = len([t for t in trades if t['type'] == 'sell' and t['profit'] > 0])
    
    return {
        'baseline_volume': baseline_volume,
        'trades': trades,
        'total_trades': len(trades),
        'winning_trades': winning_trades,
        'total_profit': total_profit_percentage,
        'total_profit_amount': total_profit,
        'final_budget': available_budget,
        'initial_budget': initial_budget,
        'milestones': milestones
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
        alpha_vantage = get_alpha_vantage()
        if not alpha_vantage:
            return render_template('analysis_dashboard.html', 
                                alpha_vantage_available=False,
                                error="Alpha Vantage API not configured")
        
        # Define stocks to analyze
        stocks = ['TSLA', 'NVDA', 'AAPL']
        stock_data = {}
        simulation_results = {}
        
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
                    # Run simulation
                    simulation_results[symbol] = simulate_volume_trading(stock_data[symbol])
            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {str(e)}")
                stock_data[symbol] = []
                simulation_results[symbol] = None
        
        return render_template('analysis_dashboard.html', 
                            alpha_vantage_available=True,
                            stock_data=stock_data,
                            simulation_results=simulation_results,
                            active_tab='volume')
    except Exception as e:
        logger.error(f"Error in volume_analysis route: {str(e)}")
        flash(f"Error loading volume analysis page: {str(e)}", "error")
        return render_template('analysis_dashboard.html', 
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