from schwab_trader.routes.root import root_bp
from schwab_trader.routes.analysis_dashboard import bp as analysis_dashboard_bp
from schwab_trader.routes.analysis import analysis_bp

# Register blueprints
app.register_blueprint(root_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(analysis_bp, url_prefix='/analysis')
app.register_blueprint(analysis_dashboard_bp) 