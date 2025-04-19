"""Example volume-based trading strategy."""
import pandas as pd
import numpy as np
from typing import List, Dict
from datetime import datetime

def volume_strategy(data: pd.DataFrame, timestamp: datetime) -> List[Dict]:
    """Volume-based trading strategy with realistic signals."""
    signals = []
    
    # Calculate volume indicators
    current_volume = data.loc[timestamp, 'Volume']
    volume_ma = data.loc[timestamp, 'Volume_MA']
    liquidity = data.loc[timestamp, 'Liquidity']
    
    # Calculate price momentum
    price = data.loc[timestamp, 'Close']
    price_ma_20 = data.loc[:timestamp, 'Close'].rolling(window=20).mean().iloc[-1]
    price_ma_50 = data.loc[:timestamp, 'Close'].rolling(window=50).mean().iloc[-1]
    
    # Volume breakout signal
    if current_volume > volume_ma * 1.5:  # 50% above average volume
        # Check price momentum
        if price > price_ma_20 and price_ma_20 > price_ma_50:
            # Strong uptrend with high volume
            signals.append({
                'action': 'buy',
                'risk': 0.15,  # 15% of portfolio
                'reason': 'Volume breakout with uptrend'
            })
        elif price < price_ma_20 and price_ma_20 < price_ma_50:
            # Strong downtrend with high volume
            signals.append({
                'action': 'sell',
                'reason': 'Volume breakout with downtrend'
            })
    
    # Low volume consolidation signal
    elif current_volume < volume_ma * 0.5:  # 50% below average volume
        if abs(price - price_ma_20) / price < 0.02:  # Price within 2% of 20MA
            signals.append({
                'action': 'sell',
                'reason': 'Low volume consolidation'
            })
    
    # Liquidity-based position sizing
    for signal in signals:
        if signal['action'] == 'buy':
            # Adjust position size based on liquidity
            if liquidity < 0.5:
                signal['risk'] *= 0.5  # Reduce position size in low liquidity
            elif liquidity > 2.0:
                signal['risk'] *= 1.2  # Increase position size in high liquidity
    
    return signals

def momentum_strategy(data: pd.DataFrame, timestamp: datetime) -> List[Dict]:
    """Momentum-based trading strategy."""
    signals = []
    
    # Calculate momentum indicators
    price = data.loc[timestamp, 'Close']
    rsi = calculate_rsi(data.loc[:timestamp, 'Close'])
    macd, signal_line = calculate_macd(data.loc[:timestamp, 'Close'])
    
    # RSI signals
    if rsi < 30:  # Oversold
        signals.append({
            'action': 'buy',
            'risk': 0.1,
            'reason': 'RSI oversold'
        })
    elif rsi > 70:  # Overbought
        signals.append({
            'action': 'sell',
            'reason': 'RSI overbought'
        })
    
    # MACD signals
    if macd > signal_line and macd < 0:  # Bullish crossover below zero
        signals.append({
            'action': 'buy',
            'risk': 0.15,
            'reason': 'MACD bullish crossover'
        })
    elif macd < signal_line and macd > 0:  # Bearish crossover above zero
        signals.append({
            'action': 'sell',
            'reason': 'MACD bearish crossover'
        })
    
    return signals

def calculate_rsi(prices: pd.Series, period: int = 14) -> float:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[float, float]:
    """Calculate MACD indicator."""
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd.iloc[-1], signal_line.iloc[-1] 