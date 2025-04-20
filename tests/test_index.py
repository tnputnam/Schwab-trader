import pytest
from flask import url_for
from schwab_trader import create_app, db
from schwab_trader.utils.logger import setup_logger

logger = setup_logger(__name__)

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test',
        'ALPHA_VANTAGE_API_KEY': 'test',
        'SCHWAB_API_KEY': 'test',
        'SCHWAB_API_SECRET': 'test'
    })
    
    with app.app_context():
        try:
            db.create_all()
            logger.info("Test database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating test database: {str(e)}")
            raise
    
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

def test_index_page(client):
    """Test that the index page loads successfully."""
    try:
        response = client.get('/')
        assert response.status_code == 200
        logger.info("Index page loaded successfully")
    except Exception as e:
        logger.error(f"Error loading index page: {str(e)}")
        raise

def test_api_initialization(app):
    """Test that APIs are properly initialized."""
    with app.app_context():
        try:
            from schwab_trader.utils.alpha_vantage_api import AlphaVantageAPI
            from schwab_trader.utils.schwab_api import SchwabAPI
            
            alpha_vantage = AlphaVantageAPI()
            alpha_vantage.init_app(app)
            assert hasattr(app, 'alpha_vantage')
            logger.info("AlphaVantage API initialized successfully")
            
            schwab = SchwabAPI()
            schwab.init_app(app)
            assert hasattr(app, 'schwab')
            logger.info("Schwab API initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing APIs: {str(e)}")
            raise

def test_database_connection(app):
    """Test database connection and operations."""
    with app.app_context():
        try:
            # Test a simple database operation
            from schwab_trader.models import User
            user = User(username='test', email='test@example.com')
            db.session.add(user)
            db.session.commit()
            assert User.query.filter_by(username='test').first() is not None
            logger.info("Database operations successful")
        except Exception as e:
            logger.error(f"Error with database operations: {str(e)}")
            raise 