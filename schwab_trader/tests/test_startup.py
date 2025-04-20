"""Test the application startup and configuration."""
import os
import tempfile
import pytest
from schwab_trader import create_app, db
from schwab_trader.utils.error_handling import setup_logging

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create a temporary file to store the database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SCHWAB_CLIENT_ID': 'test-client-id',
        'SCHWAB_CLIENT_SECRET': 'test-client-secret',
        'SCHWAB_REDIRECT_URI': 'http://localhost:5000/auth/callback',
        'CACHE_TYPE': 'SimpleCache'
    })
    
    # Create the database and load test data
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_create_app(app):
    """Test that the application can be created with test configuration."""
    assert app is not None
    assert app.config['TESTING'] is True
    assert app.config['SECRET_KEY'] == 'test-key'
    assert 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']

def test_app_context(app):
    """Test that the application context works."""
    with app.app_context():
        assert app.config['TESTING'] is True
        assert db.engine is not None

def test_logging_setup(app):
    """Test that logging can be set up."""
    with app.app_context():
        setup_logging(app)
        assert app.logger is not None
        assert app.logger.level == 20  # INFO level 