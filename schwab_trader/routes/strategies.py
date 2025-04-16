from flask import Blueprint, render_template, jsonify
import logging
from datetime import datetime

bp = Blueprint('strategies', __name__, url_prefix='/strategies')

# Configure route-specific logger
logger = logging.getLogger('strategies_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/')
def index():
    """Display the strategies page."""
    logger.info('Accessing strategies page')
    try:
        return render_template('strategies.html')
    except Exception as e:
        logger.error(f'Error rendering strategies page: {str(e)}')
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/list')
def list_strategies():
    """Get list of available strategies."""
    logger.info('Fetching strategies list')
    try:
        # Mock data for now
        strategies = [
            {
                'name': 'Moving Average Crossover',
                'description': 'Strategy based on moving average crossovers',
                'status': 'active'
            }
        ]
        return jsonify(strategies)
    except Exception as e:
        logger.error(f'Error fetching strategies: {str(e)}')
        return jsonify({'error': 'Failed to fetch strategies'}), 500 