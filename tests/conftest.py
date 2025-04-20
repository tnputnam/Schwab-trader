import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_caching import Cache
from flask_login import LoginManager
from schwab_trader import create_app, db
from schwab_trader.models import User
from unittest.mock import MagicMock

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
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key',
        'ALPHA_VANTAGE_API_KEY': 'test_key'
    }
    
    app = create_app(test_config)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create all tables
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def session(app):
    """Create a new database session for a test."""
    with app.app_context():
        yield db.session

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
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