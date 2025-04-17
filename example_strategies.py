import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def moving_average_crossover_strategy(data: pd.DataFrame) -> str:
    """
    Simple moving average crossover strategy
    Buy when 20-day SMA crosses above 50-day SMA
    Sell when 20-day SMA crosses below 50-day SMA
    """
    if len(data) < 50:
        return 'HOLD'
    
    # Get the last two days of data
    last_two = data.tail(2)
    
    # Check for crossover
    if (last_two['SMA_20'].iloc[-2] < last_two['SMA_50'].iloc[-2] and 
        last_two['SMA_20'].iloc[-1] > last_two['SMA_50'].iloc[-1]):
        return 'BUY'
    elif (last_two['SMA_20'].iloc[-2] > last_two['SMA_50'].iloc[-2] and 
          last_two['SMA_20'].iloc[-1] < last_two['SMA_50'].iloc[-1]):
        return 'SELL'
    
    return 'HOLD'

def rsi_strategy(data: pd.DataFrame, 
                overbought: float = 70, 
                oversold: float = 30) -> str:
    """
    RSI strategy
    Buy when RSI crosses below oversold level
    Sell when RSI crosses above overbought level
    """
    if len(data) < 14:
        return 'HOLD'
    
    # Get the last two days of data
    last_two = data.tail(2)
    
    # Check for RSI signals
    if (last_two['RSI'].iloc[-2] > oversold and 
        last_two['RSI'].iloc[-1] < oversold):
        return 'BUY'
    elif (last_two['RSI'].iloc[-2] < overbought and 
          last_two['RSI'].iloc[-1] > overbought):
        return 'SELL'
    
    return 'HOLD'

def bollinger_bands_strategy(data: pd.DataFrame) -> str:
    """
    Bollinger Bands strategy
    Buy when price crosses below lower band
    Sell when price crosses above upper band
    """
    if len(data) < 20:
        return 'HOLD'
    
    # Get the last two days of data
    last_two = data.tail(2)
    
    # Check for band crossings
    if (last_two['Close'].iloc[-2] > last_two['BB_lower'].iloc[-2] and 
        last_two['Close'].iloc[-1] < last_two['BB_lower'].iloc[-1]):
        return 'BUY'
    elif (last_two['Close'].iloc[-2] < last_two['BB_upper'].iloc[-2] and 
          last_two['Close'].iloc[-1] > last_two['BB_upper'].iloc[-1]):
        return 'SELL'
    
    return 'HOLD'

def macd_strategy(data: pd.DataFrame) -> str:
    """
    MACD strategy
    Buy when MACD line crosses above signal line
    Sell when MACD line crosses below signal line
    """
    if len(data) < 26:
        return 'HOLD'
    
    # Calculate MACD
    exp1 = data['Close'].ewm(span=12, adjust=False).mean()
    exp2 = data['Close'].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    
    # Get the last two days
    last_two_macd = macd.tail(2)
    last_two_signal = signal.tail(2)
    
    # Check for crossovers
    if (last_two_macd.iloc[-2] < last_two_signal.iloc[-2] and 
        last_two_macd.iloc[-1] > last_two_signal.iloc[-1]):
        return 'BUY'
    elif (last_two_macd.iloc[-2] > last_two_signal.iloc[-2] and 
          last_two_macd.iloc[-1] < last_two_signal.iloc[-1]):
        return 'SELL'
    
    return 'HOLD'

def volume_strategy(data: pd.DataFrame, 
                   volume_ma_period: int = 20,
                   volume_threshold: float = 1.5) -> str:
    """
    Volume strategy
    Buy when volume is significantly above average
    Sell when volume is significantly below average
    """
    if len(data) < volume_ma_period:
        return 'HOLD'
    
    # Calculate volume moving average
    volume_ma = data['Volume'].rolling(window=volume_ma_period).mean()
    
    # Get the last day's data
    last_volume = data['Volume'].iloc[-1]
    last_volume_ma = volume_ma.iloc[-1]
    
    # Check for volume signals
    if last_volume > last_volume_ma * volume_threshold:
        return 'BUY'
    elif last_volume < last_volume_ma / volume_threshold:
        return 'SELL'
    
    return 'HOLD'

def tesla_volume_analysis(data: pd.DataFrame, volume_threshold: float = 1.15) -> dict:
    """
    Analyze Tesla's volume patterns and their impact on price.
    
    Args:
        data: DataFrame with historical data
        volume_threshold: Percentage above average volume to consider significant (default 15%)
    
    Returns:
        dict containing analysis results including:
        - monthly_avg_volume: Average volume for the month
        - high_volume_days: Number of days with volume > threshold
        - price_changes: Price changes during high volume days
        - volume_correlation: Correlation between volume and price changes
    """
    if len(data) < 20:  # Need at least 20 days of data
        return {
            'error': 'Insufficient data for analysis',
            'monthly_avg_volume': 0,
            'high_volume_days': 0,
            'price_changes': [],
            'volume_correlation': 0
        }
    
    # Calculate monthly average volume
    monthly_avg_volume = data['Volume'].mean()
    
    # Identify high volume days
    high_volume_mask = data['Volume'] > (monthly_avg_volume * volume_threshold)
    high_volume_days = data[high_volume_mask]
    
    # Calculate price changes during high volume days
    price_changes = []
    for idx, day in high_volume_days.iterrows():
        # Get next day's price change
        next_day_idx = data.index.get_loc(idx) + 1
        if next_day_idx < len(data):
            next_day = data.iloc[next_day_idx]
            price_change = ((next_day['Close'] - day['Close']) / day['Close']) * 100
            price_changes.append({
                'date': idx,
                'volume': day['Volume'],
                'price_change': price_change,
                'close_price': day['Close']
            })
    
    # Calculate correlation between volume and price changes
    volume_correlation = data['Volume'].corr(data['Close'].pct_change())
    
    return {
        'monthly_avg_volume': monthly_avg_volume,
        'high_volume_days': len(high_volume_days),
        'price_changes': price_changes,
        'volume_correlation': volume_correlation,
        'high_volume_days_data': high_volume_days[['Volume', 'Close']].to_dict('records')
    }

def volume_ratio_strategy(data, buy_threshold=1.15, sell_threshold=1.05):
    """
    Volume-based strategy that:
    1. Tracks buy/sell volume ratio over 30 days
    2. Buys when buy volume is 15% above sell volume
    3. Sells when buy volume drops below 5% above sell volume
    
    Parameters:
    - data: DataFrame with OHLCV data
    - buy_threshold: Minimum buy/sell volume ratio to trigger buy (default 1.15 = 15% above)
    - sell_threshold: Maximum buy/sell volume ratio to trigger sell (default 1.05 = 5% above)
    
    Returns:
    - tuple: (signal, decision_details)
      signal: 'BUY', 'SELL', or 'HOLD'
      decision_details: dict containing detailed information about the decision
    """
    if len(data) < 30:  # Need 30 days of data for meaningful analysis
        return 'HOLD', {'reason': 'Insufficient data', 'days_available': len(data)}
        
    # Calculate price change
    data['price_change'] = data['Close'].pct_change()
    
    # Calculate volume ratios using last 30 days
    up_volume = data[data['price_change'] > 0]['Volume'].mean()
    down_volume = data[data['price_change'] < 0]['Volume'].mean()
    
    # Calculate current volume ratio
    current_volume_ratio = up_volume / down_volume if down_volume > 0 else 0
    
    # Prepare decision details
    decision_details = {
        'current_volume_ratio': current_volume_ratio,
        'buy_threshold': buy_threshold,
        'sell_threshold': sell_threshold,
        'up_volume': up_volume,
        'down_volume': down_volume,
        'recent_price_change': data['Close'].pct_change().iloc[-1],
        'average_daily_volume': data['Volume'].mean()
    }
    
    # Generate signals based only on volume ratio
    if current_volume_ratio >= buy_threshold:
        decision_details['reason'] = f'Buy volume {current_volume_ratio:.2f}x above sell volume (threshold: {buy_threshold})'
        return 'BUY', decision_details
    elif current_volume_ratio <= sell_threshold:
        decision_details['reason'] = f'Buy volume {current_volume_ratio:.2f}x above sell volume (threshold: {sell_threshold})'
        return 'SELL', decision_details
    else:
        decision_details['reason'] = f'Volume ratio {current_volume_ratio:.2f} within normal range'
        return 'HOLD', decision_details 