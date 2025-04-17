import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import talib

class TechnicalAnalysisVisualizer:
    def __init__(self, strategy):
        self.strategy = strategy

    def create_analysis_chart(self, symbol, data, signals=None):
        """Create an interactive chart with all technical indicators"""
        # Convert data to pandas DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        
        # Calculate indicators
        prices = df['close'].values
        volumes = df['volume'].values
        
        # Calculate technical indicators using the strategy's parameters
        rsi = talib.RSI(prices, timeperiod=self.strategy.rsi_period)
        macd, macd_signal, macd_hist = talib.MACD(
            prices, 
            fastperiod=12, 
            slowperiod=26, 
            signalperiod=9
        )
        bb_upper, bb_middle, bb_lower = talib.BBANDS(
            prices,
            timeperiod=self.strategy.bollinger_period,
            nbdevup=self.strategy.bollinger_std,
            nbdevdn=self.strategy.bollinger_std
        )
        
        # Create subplots
        fig = make_subplots(
            rows=4, 
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(
                'Price and Bollinger Bands',
                'Volume',
                'RSI',
                'MACD'
            ),
            row_heights=[0.4, 0.2, 0.2, 0.2]
        )

        # Add price candlesticks
        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='Price'
            ),
            row=1, col=1
        )

        # Add Bollinger Bands
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=bb_upper,
                name='BB Upper',
                line=dict(color='gray', dash='dash')
            ),
            row=1, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=bb_lower,
                name='BB Lower',
                line=dict(color='gray', dash='dash'),
                fill='tonexty'
            ),
            row=1, col=1
        )

        # Add volume bars
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                name='Volume',
                marker_color='blue',
                opacity=0.5
            ),
            row=2, col=1
        )

        # Add RSI
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=rsi,
                name='RSI',
                line=dict(color='purple')
            ),
            row=3, col=1
        )
        
        # Add RSI levels
        fig.add_hline(
            y=self.strategy.rsi_oversold,
            line_dash="dash",
            line_color="green",
            row=3
        )
        fig.add_hline(
            y=self.strategy.rsi_overbought,
            line_dash="dash",
            line_color="red",
            row=3
        )

        # Add MACD
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=macd,
                name='MACD',
                line=dict(color='blue')
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=macd_signal,
                name='Signal',
                line=dict(color='orange')
            ),
            row=4, col=1
        )
        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=macd_hist,
                name='Histogram',
                marker_color='gray'
            ),
            row=4, col=1
        )

        # Add signals if provided
        if signals:
            buy_signals = [s for s in signals if s['action'] == 'BUY']
            sell_signals = [s for s in signals if s['action'] == 'SELL']
            
            # Add buy signals
            if buy_signals:
                buy_dates = [s['timestamp'] for s in buy_signals]
                buy_prices = [df.loc[df['date'] == d, 'close'].iloc[0] for d in buy_dates]
                fig.add_trace(
                    go.Scatter(
                        x=buy_dates,
                        y=buy_prices,
                        mode='markers',
                        name='Buy Signal',
                        marker=dict(
                            symbol='triangle-up',
                            size=15,
                            color='green'
                        )
                    ),
                    row=1, col=1
                )
            
            # Add sell signals
            if sell_signals:
                sell_dates = [s['timestamp'] for s in sell_signals]
                sell_prices = [df.loc[df['date'] == d, 'close'].iloc[0] for d in sell_dates]
                fig.add_trace(
                    go.Scatter(
                        x=sell_dates,
                        y=sell_prices,
                        mode='markers',
                        name='Sell Signal',
                        marker=dict(
                            symbol='triangle-down',
                            size=15,
                            color='red'
                        )
                    ),
                    row=1, col=1
                )

        # Update layout
        fig.update_layout(
            title=f'Technical Analysis for {symbol}',
            xaxis_rangeslider_visible=False,
            height=1200
        )

        return fig

    def save_chart(self, fig, filename):
        """Save the chart to an HTML file"""
        fig.write_html(filename)
