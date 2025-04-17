from flask import Flask, render_template, request, jsonify
import os
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, 
    template_folder='schwab_trader/templates',
    static_folder='schwab_trader/static'
)

@app.route('/')
def home():
    return "Home page"

@app.route('/test')
def test():
    return "Test route working!"

@app.route('/test_alpha_vantage')
def test_alpha_vantage():
    try:
        return render_template('test_alpha_vantage.html')
    except Exception as e:
        return str(e), 500

@app.route('/api/test_alpha_vantage', methods=['POST'])
def test_alpha_vantage_api():
    """Test Alpha Vantage API endpoint"""
    logger.info("Testing Alpha Vantage API")
    try:
        data = request.get_json()
        symbol = data.get('symbol', 'AAPL')
        
        # Get API key
        api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not api_key:
            logger.error("Alpha Vantage API key not found")
            return jsonify({
                'status': 'error',
                'message': 'Alpha Vantage API key not found in environment'
            }), 400
        
        logger.info(f"Testing Alpha Vantage API for symbol: {symbol}")
        logger.info(f"Using API key: {api_key[:5]}...")
        
        # Test TIME_SERIES_DAILY endpoint
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&outputsize=compact&apikey={api_key}"
        logger.info(f"Request URL: {url}")
        
        try:
            response = requests.get(url, timeout=10)
            logger.info(f"Response status: {response.status_code}")
            logger.info(f"Response content: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                if 'Error Message' in data:
                    logger.error(f"Alpha Vantage error: {data['Error Message']}")
                    return jsonify({
                        'status': 'error',
                        'message': data['Error Message']
                    }), 400
                elif 'Note' in data:
                    logger.warning(f"Alpha Vantage note: {data['Note']}")
                    return jsonify({
                        'status': 'warning',
                        'message': data['Note']
                    }), 200
                else:
                    return jsonify({
                        'status': 'success',
                        'data': data
                    })
            else:
                logger.error(f"HTTP Error: {response.status_code}")
                return jsonify({
                    'status': 'error',
                    'message': f"HTTP Error: {response.status_code}",
                    'response': response.text
                }), response.status_code
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    print("\nStarting test server on port 5002...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Template folder: {app.template_folder}")
    app.run(host='0.0.0.0', port=5002, debug=True) 