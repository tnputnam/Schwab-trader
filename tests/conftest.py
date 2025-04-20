import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_caching import Cache
from flask_login import LoginManager
from schwab_trader import create_app, db
from schwab_trader.models import User

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for each test session."""
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test-secret-key'
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
        password='testpass'
    )
    session.add(user)
    session.commit()
    return user