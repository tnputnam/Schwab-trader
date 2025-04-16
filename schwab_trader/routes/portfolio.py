from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import pandas as pd
import os
from datetime import datetime
import logging

bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')

# Configure logging
logger = logging.getLogger('portfolio_routes')
handler = logging.FileHandler('logs/portfolio_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/')
@login_required
def portfolio():
    """Display the portfolio page."""
    return render_template('portfolio.html')

@bp.route('/import', methods=['POST'])
@login_required
def import_portfolio():
    """Import portfolio data from Schwab."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
            
        # Read the CSV file
        df = pd.read_csv(file)
        
        # Expected columns from Schwab positions page
        expected_columns = [
            'Symbol', 'Description', 'Quantity', 'Last Price', 
            'Average Cost', 'Market Value', 'Day Change $', 'Day Change %'
        ]
        
        # Validate required columns
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            return jsonify({
                'success': False, 
                'error': f'Missing required columns: {", ".join(missing_columns)}'
            })
        
        # Clean and format the data
        portfolio_data = []
        for _, row in df.iterrows():
            position = {
                'symbol': row['Symbol'],
                'description': row['Description'],
                'quantity': float(row['Quantity']),
                'last_price': float(row['Last Price'].replace('$', '').replace(',', '')),
                'avg_cost': float(row['Average Cost'].replace('$', '').replace(',', '')),
                'market_value': float(row['Market Value'].replace('$', '').replace(',', '')),
                'day_change_dollar': float(row['Day Change $'].replace('$', '').replace(',', '')),
                'day_change_percent': float(row['Day Change %'].replace('%', ''))
            }
            portfolio_data.append(position)
        
        # Calculate portfolio totals
        total_value = sum(pos['market_value'] for pos in portfolio_data)
        total_change = sum(pos['day_change_dollar'] for pos in portfolio_data)
        total_change_percent = (total_change / (total_value - total_change)) * 100 if total_value > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'positions': portfolio_data,
                'summary': {
                    'total_value': total_value,
                    'total_change_dollar': total_change,
                    'total_change_percent': total_change_percent,
                    'last_updated': datetime.now().isoformat()
                }
            }
        })
        
    except Exception as e:
        logger.error(f'Error importing portfolio: {str(e)}')
        return jsonify({
            'success': False,
            'error': f'Error processing file: {str(e)}'
        }) 