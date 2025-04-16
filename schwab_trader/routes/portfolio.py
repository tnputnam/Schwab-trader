from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
import pandas as pd
import os
from datetime import datetime
import logging
from schwab_trader.models import db, Portfolio, Position, Sector
from collections import defaultdict

bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')

# Configure logging
logger = logging.getLogger('portfolio_routes')
handler = logging.FileHandler('logs/portfolio_{}.log'.format(datetime.now().strftime('%Y%m%d')))
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

@bp.route('/')
def view():
    """Display portfolio view."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return render_template('portfolio.html', error="No portfolio found")
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    
    # Calculate sector allocation
    sector_totals = defaultdict(float)
    asset_type_totals = defaultdict(float)
    
    for position in positions:
        sector_totals[position.sector or 'Uncategorized'] += position.market_value
        asset_type_totals[position.security_type or 'Other'] += position.market_value
    
    total_value = sum(sector_totals.values())
    
    # Convert to percentages
    sector_data = {
        'labels': list(sector_totals.keys()),
        'values': [value / total_value * 100 for value in sector_totals.values()]
    }
    
    asset_type_data = {
        'labels': list(asset_type_totals.keys()),
        'values': [value / total_value * 100 for value in asset_type_totals.values()]
    }
    
    return render_template('portfolio.html',
                         portfolio=portfolio,
                         positions=positions,
                         sector_labels=sector_data['labels'],
                         sector_values=sector_data['values'],
                         asset_type_labels=asset_type_data['labels'],
                         asset_type_values=asset_type_data['values'])

@bp.route('/api/summary')
def get_summary():
    """Get portfolio summary data."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    return jsonify({
        'total_value': portfolio.total_value,
        'cash_value': portfolio.cash_value,
        'day_change': portfolio.day_change,
        'day_change_percent': portfolio.day_change_percent,
        'total_gain': portfolio.total_gain,
        'total_gain_percent': portfolio.total_gain_percent
    })

@bp.route('/api/positions')
def get_positions():
    """Get all portfolio positions."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    return jsonify([{
        'symbol': p.symbol,
        'description': p.description,
        'quantity': p.quantity,
        'price': p.price,
        'market_value': p.market_value,
        'cost_basis': p.cost_basis,
        'day_change_dollar': p.day_change_dollar,
        'day_change_percent': p.day_change_percent,
        'security_type': p.security_type,
        'sector': p.sector
    } for p in positions])

@bp.route('/api/sectors')
def get_sectors():
    """Get sector allocation data."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    sectors = Sector.query.filter_by(portfolio_id=portfolio.id).all()
    return jsonify([{
        'name': s.name,
        'market_value': s.market_value,
        'percentage': s.percentage
    } for s in sectors])

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