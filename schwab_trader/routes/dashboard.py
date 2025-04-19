from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
import yfinance as yf
from datetime import datetime, timedelta
import logging
import os
import requests
from schwab_trader.services.alpha_vantage import AlphaVantageAPI
import pandas as pd
import numpy as np
from schwab_trader.services.logging_service import LoggingService

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')
logger = LoggingService()

# Initialize Alpha Vantage API
alpha_vantage = AlphaVantageAPI()

@bp.route('/')
def index():
    """Dashboard page."""
    try:
        return render_template('market_dashboard.html')
    except Exception as e:
        logger.error(f"Error in dashboard route: {str(e)}")
        return render_template('market_dashboard.html')

@bp.route('/portfolio')
def portfolio():
    """Portfolio page."""
    try:
        return render_template('portfolio.html')
    except Exception as e:
        logger.error(f"Error in portfolio route: {str(e)}")
        return render_template('portfolio.html')

@bp.route('/trading')
def trading():
    """Display the trading dashboard."""
    return render_template('trading_dashboard.html')

@bp.route('/volume_analysis')
def volume_analysis():
    """Display the volume analysis dashboard."""
    if 'schwab_token' not in session:
        return redirect(url_for('auth.schwab_auth'))
    return render_template('tesla_dashboard.html')

@bp.route('/api/paper_trade', methods=['POST'])
def paper_trade():
    """Handle paper trading requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        # Process paper trade request
        # Implementation details here
        
        return jsonify({'message': 'Paper trade executed successfully'})
    except Exception as e:
        logger.error(f"Error in paper_trade route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/search_symbols', methods=['POST'])
def search_symbols():
    """Search for stock symbols."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'No search query provided'}), 400
            
        # Search symbols using AlphaVantage
        results = alpha_vantage.search_symbols(data['query'])
        
        return jsonify({'results': results})
    except Exception as e:
        logger.error(f"Error in search_symbols route: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage():
    """Test Alpha Vantage API connection."""
    try:
        symbol = request.json.get('symbol', 'AAPL')
        response = alpha_vantage.get_quote(symbol)
        
        if 'Note' in response:
            return jsonify({
                'status': 'warning',
                'message': response['Note']
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'data': response
            })
    except Exception as e:
        logger.error(f"Error testing Alpha Vantage: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@bp.route('/api/status')
def api_status():
    """Mock API health check endpoint."""
    try:
        # Simulate API response with mock data
        mock_response = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'schwab_api': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                },
                'alpha_vantage': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                },
                'yfinance': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                }
            }
        }
        return jsonify(mock_response)
    except Exception as e:
        logger.error(f"Error in mock API status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def generate_market_data(symbol, market_condition, base_price):
    """Generate market data for a specific condition using historical market-wide periods."""
    import pandas as pd
    import numpy as np
    from datetime import datetime, timedelta
    
    # Define market-wide historical periods that best represent each condition
    market_periods = {
        'bearish': ('2022-01-01', '2022-12-31'),  # 2022 Market Downturn
        'bullish': ('2020-04-01', '2021-03-31'),  # Post-COVID Recovery Rally
        'neutral': ('2021-07-01', '2022-06-30')   # 2021-22 Market Consolidation
    }
    
    # Get the specific period for this market condition
    start_date, end_date = market_periods[market_condition]
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Create date range
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Set market condition parameters based on overall market conditions
    if market_condition == 'bearish':
        daily_change_mean = -0.3  # Average daily decline
        daily_change_std = 2.5    # Higher volatility in bear markets
        price_range = (base_price * 0.5, base_price * 1.1)  # Significant downside
    elif market_condition == 'bullish':
        daily_change_mean = 0.4   # Average daily gain
        daily_change_std = 2.0    # Moderate volatility in bull markets
        price_range = (base_price * 0.9, base_price * 1.8)  # Strong upside
    else:  # neutral
        daily_change_mean = 0.0   # Flat average
        daily_change_std = 1.5    # Lower volatility
        price_range = (base_price * 0.8, base_price * 1.2)  # Tight range
    
    # Generate price data
    prices = []
    current_price = base_price
    
    for date in dates:
        # Generate daily price movement based on market condition
        daily_change = np.random.normal(daily_change_mean, daily_change_std)
        current_price += daily_change
        current_price = max(price_range[0], min(price_range[1], current_price))
        
        # Generate volume with some randomness
        base_volume = 100000000  # 100M shares
        volume = int(base_volume * (1 + np.random.normal(0, 0.3)))
        
        # Calculate OHLC
        open_price = current_price
        high_price = current_price * (1 + abs(np.random.normal(0, 0.02)))
        low_price = current_price * (1 - abs(np.random.normal(0, 0.02)))
        close_price = current_price
        
        prices.append({
            'date': date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
    
    return prices, start_date, end_date

@bp.route('/api/test_data/<symbol>/<market_condition>')
def get_test_data(symbol, market_condition):
    """Serve test historical data for a symbol with specific market condition."""
    try:
        # Base prices for different stocks
        base_prices = {
            'TSLA': 180.0,
            'NVDA': 400.0,
            'AMZN': 120.0,
            'AAPL': 170.0
        }
        
        if symbol not in base_prices:
            return jsonify({
                'status': 'error',
                'message': f'Unsupported symbol: {symbol}'
            }), 400
            
        if market_condition not in ['bearish', 'bullish', 'neutral']:
            return jsonify({
                'status': 'error',
                'message': 'Market condition must be bearish, bullish, or neutral'
            }), 400
        
        # Generate data
        prices, start_date, end_date = generate_market_data(symbol, market_condition, base_prices[symbol])
        
        # Generate trades based on market condition
        trades = []
        num_trades = 15 if market_condition == 'neutral' else 10
        
        for _ in range(num_trades):
            trade_date = np.random.choice(pd.date_range(start=start_date, end=end_date, freq='D'))
            
            # Adjust trade type probability based on market condition
            if market_condition == 'bearish':
                trade_type = np.random.choice(['buy', 'sell'], p=[0.7, 0.3])
            elif market_condition == 'bullish':
                trade_type = np.random.choice(['buy', 'sell'], p=[0.3, 0.7])
            else:
                trade_type = np.random.choice(['buy', 'sell'], p=[0.5, 0.5])
            
            trade_price = np.random.uniform(
                min(p['low'] for p in prices),
                max(p['high'] for p in prices)
            )
            trade_volume = int(np.random.uniform(100, 1000))
            
            trades.append({
                'date': trade_date.strftime('%Y-%m-%d'),
                'type': trade_type,
                'price': round(trade_price, 2),
                'volume': trade_volume
            })
        
        mock_data = {
            'prices': prices,
            'trades': trades,
            'market_condition': market_condition,
            'symbol': symbol,
            'period': {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
        }
        
        # Log the data generation
        logger.info(f"Generated {market_condition} market data for {symbol}")
        logger.info(f"Market Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        logger.info(f"Price range: ${min(p['low'] for p in prices):.2f} - ${max(p['high'] for p in prices):.2f}")
        logger.info(f"Generated {len(trades)} trades")
        
        return jsonify({
            'status': 'success',
            'data': mock_data
        })
    except Exception as e:
        logger.error(f"Error serving test data: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500 