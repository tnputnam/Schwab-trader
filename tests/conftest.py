import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_caching import Cache
from flask_login import LoginManager
from schwab_trader import create_app, db
from schwab_trader.models import User
from unittest.mock import MagicMock
import os
import tempfile
from schwab_trader.services.market_data_service import MarketDataService

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    ALPHA_VANTAGE_API_KEY = 'test_key'

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'WTF_CSRF_ENABLED': False,
        'SCHWAB_CLIENT_ID': 'test_client_id',
        'SCHWAB_CLIENT_SECRET': 'test_client_secret',
        'SCHWAB_REDIRECT_URI': 'http://localhost:5000/auth/callback',
        'SCHWAB_AUTH_URL': 'https://api.schwabapi.com/v1/oauth/authorize',
        'SCHWAB_TOKEN_URL': 'https://api.schwabapi.com/v1/oauth/token',
        'SCHWAB_SCOPES': 'read_accounts trade read_positions',
        'SCHWAB_API_BASE_URL': 'https://api.schwabapi.com/v1',
        'ALPHA_VANTAGE_API_KEY': 'test_api_key',
        'SECRET_KEY': 'test-secret-key'
    })
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture(scope='function')
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        # Clear all tables before each test
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        
        yield db.session
        
        # Clean up after test
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture
def cache(app):
    return Cache(app)

@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        name='Test User'
    )
    user.set_password('password')  # Set a password for the test user
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def mock_market_data():
    """Fixture to provide mock market data for tests."""
    return {
        'symbol': 'AAPL',
        'price': 150.00,
        'volume': 1000000,
        'change': 2.5,
        'market_cap': 2500000000000,
        'pe_ratio': 25.5,
        'dividend_yield': 0.65
    }

@pytest.fixture
def mock_analysis_service(app):
    """Fixture to provide a mock analysis service."""
    with app.app_context():
        service = MagicMock()
        service.get_market_status.return_value = True
        service.get_volume_analysis.return_value = {
            'average_volume': 1000000,
            'volume_trend': 'increasing'
        }
        return service

@pytest.fixture
def market_data_service(app):
    """A test market data service."""
    with app.app_context():
        service = MarketDataService()
        yield service

@pytest.fixture
def live_server(app, request):
    """Create a live server for Selenium tests."""
    server = request.getfixturevalue('live_server')
    return server