from flask import Blueprint, render_template, jsonify, current_app, request
import logging
from datetime import datetime
from functools import wraps
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import requests
from typing import Dict, List, Optional

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
def market_news():
    """Get market news data."""
    logger.info('Fetching market news')
    api_key = validate_api_key()
    
    # TODO: Implement actual news API integration
    news = [
        {
            'title': 'Market Update',
            'description': 'Latest market movements and analysis',
            'source': 'Financial Times',
            'published_at': datetime.now().isoformat(),
            'category': 'market'
        }
    ]
    return jsonify(news)

@bp.route('/headlines')
@limiter.limit("10 per minute")
@handle_errors
def headlines():
    """Get top business headlines."""
    logger.info('Fetching business headlines')
    api_key = validate_api_key()
    
    # TODO: Implement actual news API integration
    headlines = [
        {
            'title': 'Business Update',
            'description': 'Latest business news and updates',
            'source': 'Bloomberg',
            'published_at': datetime.now().isoformat(),
            'category': 'business'
        }
    ]
    return jsonify(headlines)

@bp.route('/search')
@limiter.limit("20 per minute")
@handle_errors
def search_news():
    """Search for news articles."""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 10))
    
    if not query:
        raise NewsError('Search query is required', 'INVALID_INPUT', 400)
    
    api_key = validate_api_key()
    
    # TODO: Implement actual news API search
    results = {
        'total': 1,
        'page': page,
        'per_page': per_page,
        'articles': [
            {
                'title': f'Search result for: {query}',
                'description': 'This is a mock search result',
                'source': 'Search API',
                'published_at': datetime.now().isoformat(),
                'category': category or 'general'
            }
        ]
    }
    return jsonify(results) 