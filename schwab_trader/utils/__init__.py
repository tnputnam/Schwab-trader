"""
Utility modules for Schwab Trader.
"""

from .logger import setup_logger
from .error_utils import (
    APIError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)
from .alpha_vantage import AlphaVantageAPI
from .schwab_api import SchwabAPI
from .schwab_oauth import SchwabOAuth
from .auth_decorators import require_schwab_auth, require_schwab_token
from .config_utils import get_config
from .data_validation import DataValidator
from .api_utils import retry_on_failure, cache_response, handle_api_error
from .visualization import TechnicalAnalysisVisualizer
from .backtester import StrategyBacktester

__all__ = [
    'AlphaVantageAPI',
    'SchwabAPI',
    'SchwabOAuth',
    'require_schwab_auth',
    'require_schwab_token',
    'APIError',
    'ValidationError',
    'setup_logger',
    'get_config',
    'DataValidator',
    'retry_on_failure',
    'cache_response',
    'handle_api_error',
    'TechnicalAnalysisVisualizer',
    'StrategyBacktester'
]
