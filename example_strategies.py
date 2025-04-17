import pandas as pd
import numpy as np
from typing import Dict

def moving_average_crossover_strategy(df: pd.DataFrame, 
                                   short_window: int = 20,
                                   long_window: int = 50) -> Dict:
    """
    Simple moving average crossover strategy
    Buy when short MA crosses above long MA
    Sell when short MA crosses below long MA
    """
    # Calculate moving averages
    df['short_ma'] = df['Close'].rolling(window=short_window).mean()
    df['long_ma'] = df['Close'].rolling(window=long_window).mean()
    
    # Get current and previous values
    current_short = df['short_ma'].iloc[-1]
    current_long = df['long_ma'].iloc[-1]
    prev_short = df['short_ma'].iloc[-2]
    prev_long = df['long_ma'].iloc[-2]
    
    # Check for crossover
    if current_short > current_long and prev_short <= prev_long:
        return {'action': 'buy', 'quantity': 1}
    elif current_short < current_long and prev_short >= prev_long:
        return {'action': 'sell', 'quantity': 1}
    else:
        return {'action': 'hold'}

def rsi_strategy(df: pd.DataFrame, 
                rsi_period: int = 14,
                overbought: int = 70,
                oversold: int = 30) -> Dict:
    """
    RSI strategy
    Buy when RSI crosses below oversold
    Sell when RSI crosses above overbought
    """
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # Get current and previous values
    current_rsi = df['rsi'].iloc[-1]
    prev_rsi = df['rsi'].iloc[-2]
    
    # Check for signals
    if current_rsi < oversold and prev_rsi >= oversold:
        return {'action': 'buy', 'quantity': 1}
    elif current_rsi > overbought and prev_rsi <= overbought:
        return {'action': 'sell', 'quantity': 1}
    else:
        return {'action': 'hold'}

def bollinger_bands_strategy(df: pd.DataFrame,
                           window: int = 20,
                           num_std: float = 2.0) -> Dict:
    """
    Bollinger Bands strategy
    Buy when price touches lower band
    Sell when price touches upper band
    """
    # Calculate Bollinger Bands
    df['middle_band'] = df['Close'].rolling(window=window).mean()
    df['std'] = df['Close'].rolling(window=window).std()
    df['upper_band'] = df['middle_band'] + (df['std'] * num_std)
    df['lower_band'] = df['middle_band'] - (df['std'] * num_std)
    
    # Get current values
    current_price = df['Close'].iloc[-1]
    current_upper = df['upper_band'].iloc[-1]
    current_lower = df['lower_band'].iloc[-1]
    
    # Check for signals
    if current_price <= current_lower:
        return {'action': 'buy', 'quantity': 1}
    elif current_price >= current_upper:
        return {'action': 'sell', 'quantity': 1}
    else:
        return {'action': 'hold'} 