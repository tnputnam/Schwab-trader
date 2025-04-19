from flask import Blueprint, render_template, jsonify, current_app, request
import logging
from datetime import datetime
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from typing import Dict, List, Optional
from schwab_trader.utils.error_utils import handle_errors, handle_api_error, AppError
from schwab_trader.utils.logging_utils import get_logger
from schwab_trader.services.news_service import NewsService

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
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except NewsError as e:
            logger.error(f'News error in {f.__name__}: {str(e)}')
            return jsonify({
                'status': 'error',
                'code': e.code,
                'message': e.message,
                'details': str(e)
            }), e.status_code
        except Exception as e:
            logger.error(f'Unexpected error in {f.__name__}: {str(e)}')
            return jsonify({
                'status': 'error',
                'code': 'INTERNAL_ERROR',
                'message': 'An unexpected error occurred',
                'details': str(e)
            }), 500
    return decorated_function

def validate_api_key():
    api_key = current_app.config.get('NEWS_API_KEY')
    if not api_key:
        raise NewsError('News API key not configured', 'API_KEY_MISSING', 500)
    return api_key

@bp.route('/')
def news_feed():
    """Display the news feed page."""
    logger.info('Accessing news feed page')
    return render_template('news.html')

@bp.route('/market')
@limiter.limit("10 per minute")
@handle_errors
def get_market_news():
    """Get market news."""
    try:
        news = news_service.get_market_news()
        return jsonify({
            'status': 'success',
            'data': news
        })
    except Exception as e:
        raise AppError(
            message="Failed to fetch market news",
            status_code=500,
            code="MARKET_NEWS_ERROR",
            details=str(e)
        )

@bp.route('/headlines')
@limiter.limit("10 per minute")
@handle_errors
def get_business_headlines():
    """Get business headlines."""
    try:
        headlines = news_service.get_business_headlines()
        return jsonify({
            'status': 'success',
            'data': headlines
        })
    except Exception as e:
        raise AppError(
            message="Failed to fetch business headlines",
            status_code=500,
            code="HEADLINES_ERROR",
            details=str(e)
        )

@bp.route('/search')
@limiter.limit("20 per minute")
@handle_errors
def search_news():
    """Search news articles."""
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        raise AppError(
            message="Search query is required",
            status_code=400,
            code="MISSING_QUERY"
        )
    
    try:
        results = news_service.search_news(query, page, per_page)
        return jsonify({
            'status': 'success',
            'data': results
        })
    except Exception as e:
        raise AppError(
            message="Failed to search news",
            status_code=500,
            code="SEARCH_ERROR",
            details=str(e)
        )

@bp.route('/api/test_alpha_vantage')
@handle_api_error
@handle_errors
def test_alpha_vantage_api():
    """Test Alpha Vantage API endpoint."""
    try:
        response = news_service.test_alpha_vantage()
        return jsonify({
            'status': 'success',
            'data': response
        })
    except Exception as e:
        raise AppError(
            message="Failed to test Alpha Vantage API",
            status_code=500,
            code="API_TEST_ERROR",
            details=str(e)
        ) 