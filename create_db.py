"""Database initialization script for Schwab Trader."""
import os
import sys
from pathlib import Path
from flask_migrate import Migrate
from schwab_trader import create_app, db
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)

def init_db():
    """Initialize the database."""
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Create the Flask application
        app = create_app()
        
        # Initialize Flask-Migrate
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Check if database exists
            db_file = Path(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            if db_file.exists():
                logger.info("Database already exists. Running migrations...")
                # Run migrations
                os.system('flask db upgrade')
            else:
                logger.info("Creating new database...")
                # Create all tables
                db.create_all()
                # Initialize migrations
                os.system('flask db init')
                os.system('flask db migrate -m "Initial migration"')
                os.system('flask db upgrade')
            
            logger.info("Database initialized successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False

if __name__ == '__main__':
    if init_db():
        sys.exit(0)
    else:
        sys.exit(1) 