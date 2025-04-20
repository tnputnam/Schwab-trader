from auth_app import app, socketio

if __name__ == '__main__':
    with app.app_context():
        # Initialize any services that need the app context here
        from schwab_trader.utils.schwab_oauth import SchwabOAuth
        from schwab_trader.utils.alpha_vantage_api import AlphaVantageAPI
        
        # Initialize services
        try:
            schwab_oauth = SchwabOAuth()
            app.config['SCHWAB_OAUTH'] = schwab_oauth
            print("INFO - Schwab API initialized successfully")
        except Exception as e:
            print(f"WARNING - Could not initialize Schwab API: {str(e)}")
        
        try:
            alpha_vantage = AlphaVantageAPI()
            app.config['ALPHA_VANTAGE'] = alpha_vantage
            print("INFO - Alpha Vantage API initialized successfully")
        except Exception as e:
            print(f"WARNING - Could not initialize Alpha Vantage: {str(e)}")
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True) 