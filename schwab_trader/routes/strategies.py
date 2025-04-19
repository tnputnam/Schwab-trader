from flask import Blueprint, render_template, jsonify, request
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService

bp = Blueprint('strategies', __name__, url_prefix='/strategies')
logger = LoggingService()

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