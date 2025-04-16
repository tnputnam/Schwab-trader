from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from datetime import datetime, timedelta
import random
import pandas as pd
import os
from werkzeug.utils import secure_filename

bp = Blueprint('compare', __name__, url_prefix='/compare')

# Allowed file extensions for portfolio imports
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_portfolio_file(file, filename):
    """Parse the uploaded portfolio file and return the portfolio data."""
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:  # Excel files
            df = pd.read_excel(file)
            
        # Validate required columns
        required_columns = ['Symbol', 'Quantity', 'Price']
        if not all(col in df.columns for col in required_columns):
            return None, "Missing required columns. File must contain: Symbol, Quantity, Price"
            
        # Calculate total value for each position
        df['Value'] = df['Quantity'] * df['Price']
        total_value = df['Value'].sum()
        
        return {
            'positions': df.to_dict('records'),
            'total_value': total_value,
            'timestamp': datetime.now().isoformat()
        }, None
    except Exception as e:
        return None, f"Error parsing file: {str(e)}"

@bp.route('/')
@login_required
def portfolio_comparison():
    return render_template('compare.html')

@bp.route('/api/data')
@login_required
def get_comparison_data():
    data = generate_mock_portfolio_data()
    return jsonify(data)

@bp.route('/api/import', methods=['POST'])
@login_required
def import_portfolio():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'})
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
        
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type. Allowed types: CSV, Excel'})
        
    portfolio_name = request.form.get('name', 'My Portfolio')
    portfolio_data, error = parse_portfolio_file(file, file.filename)
    
    if error:
        return jsonify({'success': False, 'error': error})
        
    # TODO: Save portfolio data to database
    # For now, we'll just return success
    return jsonify({
        'success': True,
        'message': f'Portfolio "{portfolio_name}" imported successfully',
        'data': portfolio_data
    })

# Mock data for demonstration
def generate_mock_portfolio_data():
    # Generate 30 days of data
    dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30)]
    dates.reverse()
    
    # Schwab portfolio (monthly changes)
    schwab_values = [10000]  # Starting value
    for i in range(1, 30):
        # Monthly changes with some daily variation
        if i % 30 == 0:  # Monthly change
            change = random.uniform(-0.05, 0.05)  # ±5% monthly change
        else:
            change = random.uniform(-0.01, 0.01)  # ±1% daily variation
        schwab_values.append(schwab_values[-1] * (1 + change))
    
    # Auto-trading portfolio (daily trades)
    auto_values = [10000]  # Starting value
    for i in range(1, 30):
        # More volatile with daily trades
        change = random.uniform(-0.03, 0.03)  # ±3% daily change
        auto_values.append(auto_values[-1] * (1 + change))
    
    return {
        'dates': dates,
        'schwab_values': schwab_values,
        'auto_values': auto_values
    } 