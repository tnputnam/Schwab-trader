"""Centralized volume analysis service."""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from schwab_trader.services.logging_service import LoggingService

class VolumeAnalysisService:
    def __init__(self):
        self.volume_baselines: Dict[str, float] = {}
        self.volume_history: Dict[str, List[float]] = {}
        self.min_volume = 100000  # Minimum volume threshold
        self.volume_increase_threshold = 1.15  # 15% above baseline
        self.volume_decrease_threshold = 1.05  # 5% above baseline
        self.lookback_days = 30  # Days to consider for baseline
        self.logger = LoggingService()

    def calculate_volume_baseline(self, volumes: List[float]) -> float:
        """Calculate volume baseline using exponential moving average."""
        if not volumes:
            self.logger.log('WARNING', "No volume data provided for baseline calculation")
            return 0.0
        
        try:
            # Use EMA to give more weight to recent volumes
            ema = pd.Series(volumes).ewm(span=self.lookback_days, adjust=False).mean()
            baseline = ema.iloc[-1]
            self.logger.log('INFO', f"Calculated volume baseline: {baseline:,.0f}", {
                'baseline': baseline,
                'lookback_days': self.lookback_days
            })
            return baseline
        except Exception as e:
            self.logger.log('ERROR', f"Error calculating volume baseline: {str(e)}", {
                'error': str(e),
                'volumes_length': len(volumes)
            })
            return 0.0

    def analyze_volume_pattern(self, symbol: str, volumes: List[float]) -> Dict:
        """Analyze volume patterns and generate detailed analysis."""
        try:
            if len(volumes) < self.lookback_days:
                self.logger.log('WARNING', f"Insufficient data for {symbol}", {
                    'symbol': symbol,
                    'days_available': len(volumes),
                    'days_required': self.lookback_days
                })
                return {
                    'error': f'Insufficient data. Need {self.lookback_days} days, got {len(volumes)}',
                    'current_volume': volumes[-1] if volumes else 0,
                    'baseline': 0,
                    'volume_ratio': 0,
                    'signal': 'HOLD'
                }

            # Update or calculate baseline
            if symbol not in self.volume_baselines:
                self.volume_baselines[symbol] = self.calculate_volume_baseline(volumes)
            
            current_volume = volumes[-1]
            baseline = self.volume_baselines[symbol]
            volume_ratio = current_volume / baseline if baseline > 0 else 0

            # Generate analysis
            analysis = {
                'current_volume': current_volume,
                'baseline': baseline,
                'volume_ratio': volume_ratio,
                'signal': 'HOLD',
                'details': {
                    'volume_trend': 'stable',
                    'volume_momentum': 0,
                    'unusual_activity': False
                }
            }

            # Calculate volume momentum (rate of change)
            if len(volumes) >= 5:
                recent_volumes = volumes[-5:]
                momentum = (recent_volumes[-1] - recent_volumes[0]) / recent_volumes[0]
                analysis['details']['volume_momentum'] = momentum

            # Determine volume trend
            if volume_ratio > self.volume_increase_threshold:
                analysis['signal'] = 'BUY'
                analysis['details']['volume_trend'] = 'increasing'
                analysis['details']['unusual_activity'] = True
                self.logger.log('INFO', f"Buy signal detected for {symbol}", {
                    'symbol': symbol,
                    'volume_ratio': volume_ratio,
                    'threshold': self.volume_increase_threshold
                })
            elif volume_ratio < 1.0:
                analysis['signal'] = 'SELL'
                analysis['details']['volume_trend'] = 'decreasing'
                self.logger.log('INFO', f"Sell signal detected for {symbol}", {
                    'symbol': symbol,
                    'volume_ratio': volume_ratio
                })
            elif volume_ratio > 1.0:
                analysis['details']['volume_trend'] = 'stable_high'

            self.logger.log('INFO', f"Volume analysis for {symbol}", {
                'symbol': symbol,
                'analysis': analysis
            })
            return analysis
        except Exception as e:
            self.logger.log('ERROR', f"Error analyzing volume pattern for {symbol}", {
                'symbol': symbol,
                'error': str(e),
                'volumes_length': len(volumes)
            })
            return {
                'error': f'Error analyzing volume pattern: {str(e)}',
                'current_volume': volumes[-1] if volumes else 0,
                'baseline': 0,
                'volume_ratio': 0,
                'signal': 'HOLD'
            }

    def get_volume_alerts(self, symbol: str) -> List[str]:
        """Generate alerts based on volume patterns."""
        alerts = []
        try:
            if symbol not in self.volume_history:
                return alerts

            analysis = self.analyze_volume_pattern(symbol, self.volume_history[symbol])
            
            if analysis['details']['unusual_activity']:
                alert = f"Unusual volume activity detected: {analysis['current_volume']:,.0f} shares ({analysis['volume_ratio']:.2f}x baseline)"
                alerts.append(alert)
                self.logger.log('WARNING', alert, {
                    'symbol': symbol,
                    'current_volume': analysis['current_volume'],
                    'volume_ratio': analysis['volume_ratio']
                })
            
            if analysis['details']['volume_momentum'] > 0.2:
                alert = f"Strong volume momentum: {analysis['details']['volume_momentum']:.1%} increase in last 5 days"
                alerts.append(alert)
                self.logger.log('INFO', alert, {
                    'symbol': symbol,
                    'momentum': analysis['details']['volume_momentum']
                })
            
            return alerts
        except Exception as e:
            self.logger.log('ERROR', f"Error generating volume alerts for {symbol}", {
                'symbol': symbol,
                'error': str(e)
            })
            return []

    def update_volume_data(self, symbol: str, new_volume: float) -> Dict:
        """Update volume data and return analysis."""
        try:
            if symbol not in self.volume_history:
                self.volume_history[symbol] = []
            
            self.volume_history[symbol].append(new_volume)
            
            # Keep only last 90 days of data
            if len(self.volume_history[symbol]) > 90:
                self.volume_history[symbol] = self.volume_history[symbol][-90:]
            
            return self.analyze_volume_pattern(symbol, self.volume_history[symbol])
        except Exception as e:
            self.logger.log('ERROR', f"Error updating volume data for {symbol}", {
                'symbol': symbol,
                'new_volume': new_volume,
                'error': str(e)
            })
            return {
                'error': f'Error updating volume data: {str(e)}',
                'current_volume': new_volume,
                'baseline': 0,
                'volume_ratio': 0,
                'signal': 'HOLD'
            } 