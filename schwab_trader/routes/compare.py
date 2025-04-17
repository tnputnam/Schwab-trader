from flask import Blueprint, render_template, jsonify, request, make_response
from datetime import datetime, timedelta
import random
import pandas as pd
import os
from werkzeug.utils import secure_filename
import traceback
# import talib
import numpy as np

bp = Blueprint('compare', __name__, url_prefix='/compare')

# Allowed file extensions for portfolio imports
ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_portfolio_file(file, filename):
    """Parse the uploaded portfolio file and return the portfolio data."""
    try:
        # Read the raw file contents first
        raw_contents = file.read()
        print("Raw file type:", type(raw_contents))
        
        # Try to decode and print the first few lines
        try:
            decoded_contents = raw_contents.decode('utf-8')
        except UnicodeDecodeError:
            try:
                decoded_contents = raw_contents.decode('latin-1')
            except:
                decoded_contents = raw_contents.decode('utf-8', errors='ignore')
        
        print("First 500 characters of file:")
        print(decoded_contents[:500])
        
        # Convert the decoded contents to a StringIO object for pandas
        from io import StringIO
        csv_buffer = StringIO(decoded_contents)
        
        # Read with pandas, printing each step
        print("Reading CSV file...")
        df = pd.read_csv(csv_buffer)
        print("CSV read complete")
        print("Initial columns:", list(df.columns))
        
        # Print the first few rows of raw data
        print("\nFirst few rows of data:")
        print(df.head())
        
        # Check exact column names and types
        print("\nColumn info:")
        print(df.info())
        
        # Required columns
        required_columns = ['Symbol', 'Qty (Quantity)', 'Price']
        
        # Print exact comparison of what we're looking for vs what we have
        print("\nLooking for these columns:", required_columns)
        print("Available columns:", list(df.columns))
        
        # Check each column with detailed debugging
        for required_col in required_columns:
            if required_col in df.columns:
                print(f"Found column: {required_col}")
            else:
                print(f"Missing column: {required_col}")
                print(f"Similar columns:", [col for col in df.columns if required_col.lower() in col.lower()])
        
        # Check for missing columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            error_msg = f"Missing required columns: {', '.join(missing_columns)}"
            print(f"Error: {error_msg}")
            return None, error_msg
            
        # If we get here, we have all required columns
        # Calculate total value for each position
        df['Value'] = df['Qty (Quantity)'].astype(float) * df['Price'].astype(float)
        total_value = df['Value'].sum()
        
        return {
            'positions': df.to_dict('records'),
            'total_value': total_value,
            'timestamp': datetime.now().isoformat()
        }, None
        
    except Exception as e:
        print(f"Exception in parse_portfolio_file:")
        traceback.print_exc()
        return None, f"Error parsing file: {str(e)}"

@bp.route('/')
def view():
    return render_template('compare.html')

@bp.route('/api/data')
def get_comparison_data():
    data = generate_mock_portfolio_data()
    return jsonify(data)

@bp.route('/api/import', methods=['POST'])
def import_portfolio():
    """Handle portfolio import."""
    try:
        print("\n=== Starting new import request ===")
        
        if 'file' not in request.files:
            print("No file in request.files")
            print("Form data:", request.form)
            print("Files:", request.files)
            return jsonify({'success': False, 'error': 'No file uploaded'})
            
        file = request.files['file']
        print(f"Received file: {file.filename}")
        
        if file.filename == '':
            print("Empty filename")
            return jsonify({'success': False, 'error': 'No file selected'})
            
        if not allowed_file(file.filename):
            print(f"Invalid file type: {file.filename}")
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed types: CSV, Excel'})
            
        portfolio_name = request.form.get('name', 'My Portfolio')
        print(f"Portfolio name: {portfolio_name}")
        
        portfolio_data, error = parse_portfolio_file(file, file.filename)
        
        if error:
            print(f"Import failed: {error}")
            return jsonify({'success': False, 'error': error})
            
        print("Import successful!")
        return jsonify({
            'success': True,
            'message': f'Portfolio "{portfolio_name}" imported successfully',
            'data': portfolio_data
        })
        
    except Exception as e:
        print("Unexpected error in import_portfolio:")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Error processing file: {str(e)}'})

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

# Create some sample data
close_prices = np.random.random(100)

# Try a simple TA-Lib function
# sma = talib.SMA(close_prices, timeperiod=20) 