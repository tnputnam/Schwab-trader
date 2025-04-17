import pandas as pd
import numpy as np

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