import pytest
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_caching import Cache
from schwab_trader import create_app, db

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300

@pytest.fixture(scope='session')
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture(scope='function')
def session(app):
    connection = db.engine.connect()
    transaction = connection.begin()
    
    # Create session factory bound to the connection
    session_factory = sessionmaker(bind=connection)
    Session = scoped_session(session_factory)
    
    # Set the session for Flask-SQLAlchemy
    db.session = Session()
    
    yield db.session
    
    # Cleanup
    db.session.close()
    transaction.rollback()
    connection.close()
    Session.remove()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def cache(app):
    return Cache(app)