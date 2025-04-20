"""
Schwab Trader package initialization.
"""

from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()

def create_app(config=None):
    app = Flask(__name__)
    
    # Apply configuration
    if config:
        app.config.update(config)
    
    # Enable CORS
    CORS(app)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    
    # Register blueprints
    from .routes.root import root_bp
    from .routes.analysis_dashboard import analysis_dashboard_bp
    
    app.register_blueprint(root_bp)
    app.register_blueprint(analysis_dashboard_bp, url_prefix='/analysis/dashboard')
    
    return app
