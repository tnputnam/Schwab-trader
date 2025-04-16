from flask import Blueprint, render_template, jsonify, current_app
from flask_login import login_required
import logging
from datetime import datetime

bp = Blueprint('news', __name__, url_prefix='/news')

# Configure route-specific logger
logger = logging.getLogger('news_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/feed')
def news_feed():
    """Display the news feed page."""
    logger.info('Accessing news feed page')
    try:
        return render_template('news.html')
    except Exception as e:
        logger.error(f'Error rendering news feed: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/market-news')
def market_news():
    """Get market news data."""
    logger.info('Fetching market news')
    try:
        # Mock data for now
        news = [
            {
                'title': 'Market Update',
                'description': 'Latest market movements and analysis',
                'source': 'Financial Times',
                'published_at': '2025-04-16 10:00:00'
            }
        ]
        return jsonify(news)
    except Exception as e:
        logger.error(f'Error fetching market news: {str(e)}')
        return jsonify({'error': 'Failed to fetch market news'}), 500

@bp.route('/headlines')
def headlines():
    """Get top business headlines."""
    logger.info('Fetching business headlines')
    try:
        # Mock data for now
        headlines = [
            {
                'title': 'Business Update',
                'description': 'Latest business news and updates',
                'source': 'Bloomberg',
                'published_at': '2025-04-16 09:00:00'
            }
        ]
        return jsonify(headlines)
    except Exception as e:
        logger.error(f'Error fetching headlines: {str(e)}')
        return jsonify({'error': 'Failed to fetch headlines'}), 500 