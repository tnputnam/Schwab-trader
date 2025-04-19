from flask import Blueprint, render_template, jsonify, current_app, request
import logging
from datetime import datetime
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from typing import Dict, List, Optional
from schwab_trader.utils.error_utils import (
    APIError,
    AuthenticationError,
    NetworkError,
    ValidationError,
    TimeoutError
)
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.services.news_service import NewsService
from schwab_trader.services.auth_service import AuthService
from flask_login import login_required, current_user

bp = Blueprint('news', __name__, url_prefix='/news')

# Configure route-specific logger
logger = logging.getLogger('news_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

class NewsError(Exception):
    def __init__(self, message: str, code: str = "NEWS_ERROR", status_code: int = 500):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(message)

def handle_errors(f):
    """Decorator to handle different types of errors."""
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AuthenticationError as e:
            logger.error(f"Authentication error: {str(e)}")
            return jsonify({
                'error': e.message,
                'status_code': 401
            }), 401
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({
                'error': e.message,
                'status_code': 400
            }), 400
        except NetworkError as e:
            logger.error(f"Network error: {str(e)}")
            return jsonify({
                'error': e.message,
                'status_code': 503
            }), 503
        except TimeoutError as e:
            logger.error(f"Timeout error: {str(e)}")
            return jsonify({
                'error': e.message,
                'status_code': 504
            }), 504
        except APIError as e:
            logger.error(f"API error: {str(e)}")
            return jsonify({
                'error': e.message,
                'status_code': e.status_code or 500
            }), e.status_code or 500
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({
                'error': 'An unexpected error occurred',
                'status_code': 500
            }), 500
    return wrapper

def validate_api_key():
    api_key = current_app.config.get('NEWS_API_KEY')
    if not api_key:
        raise NewsError('News API key not configured', 'API_KEY_MISSING', 500)
    return api_key

def development_mode():
    """Check if running in development mode."""
    return current_app.config.get('ENV') == 'development'

def ensure_valid_token():
    """Ensure the user has a valid access token."""
    if development_mode():
        return  # Skip authentication in development mode
    
    if not current_user.is_authenticated:
        raise AuthenticationError("User not authenticated")
    
    if current_user.is_token_expired():
        try:
            tokens = current_user.refresh_token()
            if not tokens:
                raise AuthenticationError("Failed to refresh token")
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthenticationError(details=str(e))

def get_access_token():
    """Get the access token, using a dummy token in development mode."""
    if development_mode():
        return "development_token"
    return current_user.access_token

@bp.route('/')
@login_required
@handle_errors
def news_feed():
    """Display the news feed page."""
    logger.info('Accessing news feed page')
    return render_template('news.html')

@bp.route('/market', methods=['GET'])
@login_required
def get_market_news():
    """Get market news."""
    try:
        limit = request.args.get('limit', default=10, type=int)
        news_service = NewsService()
        news = news_service.get_market_news(limit=limit)
        return jsonify(news)
    except APIError as e:
        logger.error(f"API error in get_market_news: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Error in get_market_news: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/headlines', methods=['GET'])
@login_required
def get_business_headlines():
    """Get business headlines."""
    try:
        limit = request.args.get('limit', default=10, type=int)
        news_service = NewsService()
        headlines = news_service.get_business_headlines(limit=limit)
        return jsonify(headlines)
    except APIError as e:
        logger.error(f"API error in get_business_headlines: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Error in get_business_headlines: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/search', methods=['GET'])
@login_required
def search_news():
    """Search news articles."""
    try:
        query = request.args.get('q', '')
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        news_service = NewsService()
        results = news_service.search_news(
            query=query,
            page=page,
            per_page=per_page
        )
        return jsonify(results)
    except APIError as e:
        logger.error(f"API error in search_news: {str(e)}")
        return jsonify({'error': str(e)}), e.status_code
    except Exception as e:
        logger.error(f"Error in search_news: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/test_api')
@login_required
@handle_errors
def test_api():
    """Test Alpha Vantage API connection."""
    ensure_valid_token()
    news_service = NewsService()
    result = news_service.test_api_connection(get_access_token())
    return jsonify(result) 