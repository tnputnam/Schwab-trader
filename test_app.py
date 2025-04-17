from flask import Flask, render_template
import os

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

if __name__ == '__main__':
    print("\nStarting test server...")
    print(f"Current directory: {os.getcwd()}")
    print(f"Template folder: {app.template_folder}")
    app.run(host='0.0.0.0', port=5000, debug=True) 