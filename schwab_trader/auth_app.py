from flask import Flask, request, session, redirect, url_for, jsonify, render_template
from schwab_trader.routes.root import root_bp
from schwab_trader.routes.analysis import analysis_bp
from schwab_trader.routes.auth import bp as auth_bp
from schwab_trader.utils.logger import setup_logger
from schwab_trader.services.schwab_service import get_schwab_oauth

logger = setup_logger('auth_app')

def init_app(app):
    """Initialize auth routes for the application."""
    @app.route('/auth/callback')
    def schwab_callback():
        """Handle the OAuth callback from Schwab."""
        try:
            schwab = get_schwab_oauth()
            token = schwab.fetch_token(request.url)
            
            if token:
                # Store the token in the session
                session['schwab_token'] = token
                
                # Get user's accounts
                accounts = schwab.get_accounts()
                if accounts:
                    session['schwab_accounts'] = accounts
                    return redirect(url_for('analysis.index'))
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to get accounts'
                    }), 500
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to get token'
                }), 500
        except Exception as e:
            logger.error(f"Error in Schwab callback: {str(e)}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/login')
    def login():
        """Login page."""
        if 'schwab_token' in session:
            return redirect(url_for('analysis.index'))
        return render_template('login.html')

    @app.route('/analysis')
    def analysis():
        """Display the analysis dashboard page"""
        if 'schwab_token' not in session:
            return redirect(url_for('login'))
        return redirect(url_for('analysis.index'))

    # Register blueprints
    app.register_blueprint(root_bp)
    app.register_blueprint(analysis_bp, url_prefix='/analysis')
    app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == '__main__':
    # Print all registered routes
    print("\nRegistered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"{rule.endpoint}: {rule.methods} {rule}")
    print("\n")
    
    # Run the app
    app.run(host='0.0.0.0', port=5000, debug=True) 