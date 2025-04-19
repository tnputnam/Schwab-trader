from flask import Blueprint, render_template, jsonify, request, session, redirect, url_for
from flask_login import login_required
import pandas as pd
import os
from datetime import datetime
from schwab_trader.services.logging_service import LoggingService
from schwab_trader.models import db, Portfolio, Position
from collections import defaultdict

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')
logger = LoggingService()

@portfolio_bp.route('/')
def index():
    """Portfolio page."""
    try:
        return render_template('portfolio.html')
    except Exception as e:
        logger.error(f"Error in portfolio route: {str(e)}")
        return render_template('portfolio.html')

@portfolio_bp.route('/api/status')
def api_status():
    """Portfolio API health check endpoint."""
    try:
        response = {
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'services': {
                'portfolio_service': {
                    'status': 'connected',
                    'last_update': datetime.now().isoformat()
                }
            }
        }
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in portfolio API status: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@portfolio_bp.route('/')
def view():
    """Display portfolio view."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return render_template('portfolio.html', error="No portfolio found")
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    
    # Calculate sector allocation
    sector_totals = defaultdict(float)
    asset_type_totals = defaultdict(float)
    total_value = 0
    
    for position in positions:
        market_value = position.quantity * position.price
        sector_totals[position.sector or 'Uncategorized'] += market_value
        asset_type_totals[position.industry or 'Other'] += market_value
        total_value += market_value
    
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

@portfolio_bp.route('/api/summary')
def get_summary():
    """Get portfolio summary data."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    total_value = sum(p.quantity * p.price for p in positions)
    day_change = sum((p.quantity * p.price) - (p.quantity * p.cost_basis) for p in positions)
    day_change_percent = (day_change / total_value * 100) if total_value > 0 else 0
    
    return jsonify({
        'total_value': total_value,
        'day_change': day_change,
        'day_change_percent': day_change_percent,
        'last_updated': datetime.now().isoformat()
    })

@portfolio_bp.route('/api/positions')
def get_positions():
    """Get all portfolio positions."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    return jsonify([{
        'symbol': p.symbol,
        'quantity': p.quantity,
        'price': p.price,
        'market_value': p.quantity * p.price,
        'cost_basis': p.cost_basis,
        'day_change': (p.price - p.cost_basis) * p.quantity,
        'day_change_percent': ((p.price - p.cost_basis) / p.cost_basis * 100) if p.cost_basis > 0 else 0,
        'sector': p.sector,
        'industry': p.industry,
        'pe_ratio': p.pe_ratio,
        'market_cap': p.market_cap,
        'dividend_yield': p.dividend_yield,
        'eps': p.eps,
        'beta': p.beta,
        'volume': p.volume
    } for p in positions])

@portfolio_bp.route('/api/sectors')
def get_sectors():
    """Get sector allocation data."""
    portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
    if not portfolio:
        return jsonify({'error': 'No portfolio found'}), 404
    
    positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
    sector_totals = defaultdict(float)
    total_value = 0
    
    for position in positions:
        market_value = position.quantity * position.price
        sector_totals[position.sector or 'Uncategorized'] += market_value
        total_value += market_value
    
    sectors = [{
        'name': sector,
        'market_value': value,
        'percentage': (value / total_value * 100) if total_value > 0 else 0
    } for sector, value in sector_totals.items()]
    
    return jsonify(sectors)

@portfolio_bp.route('/import', methods=['POST'])
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
                'quantity': float(row['Quantity']),
                'price': float(row['Last Price'].replace('$', '').replace(',', '')),
                'cost_basis': float(row['Average Cost'].replace('$', '').replace(',', '')),
                'market_value': float(row['Market Value'].replace('$', '').replace(',', '')),
                'day_change': float(row['Day Change $'].replace('$', '').replace(',', '')),
                'day_change_percent': float(row['Day Change %'].replace('%', ''))
            }
            portfolio_data.append(position)
        
        # Calculate portfolio totals
        total_value = sum(pos['market_value'] for pos in portfolio_data)
        total_change = sum(pos['day_change'] for pos in portfolio_data)
        total_change_percent = (total_change / (total_value - total_change)) * 100 if total_value > 0 else 0
        
        return jsonify({
            'success': True,
            'data': {
                'positions': portfolio_data,
                'summary': {
                    'total_value': total_value,
                    'total_change': total_change,
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