from flask import Blueprint, render_template
import logging
from datetime import datetime

# Create root blueprint
root = Blueprint('root', __name__)

# Configure route-specific logger
logger = logging.getLogger('root_routes')
handler = logging.FileHandler('logs/api_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@root.route('/')
def index():
    """Display the home page."""
    logger.info('Accessing home page')
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f'Error rendering home page: {str(e)}')
        return 'Internal server error', 500

# Import other blueprints
from . import news, strategies 