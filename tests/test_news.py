import pytest
from flask import url_for
from flask_login import LoginManager
from schwab_trader import create_app, db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        'TESTING': True,
        'SERVER_NAME': 'localhost.localdomain',
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Use in-memory SQLite for testing
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test'
    }
    
    app = create_app(test_config)
    
    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    
    @login_manager.user_loader
    def load_user(user_id):
        return None  # No user authentication needed for these tests
    
    # Create application context and database tables
    with app.app_context():
        db.create_all()  # Create all database tables
        yield app
        db.session.remove()  # Clean up the session
        db.drop_all()  # Clean up the database

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

def test_news_blueprint_registration(app):
    """Test that the news blueprint is properly registered."""
    with app.app_context():
        # Get all registered blueprints
        blueprints = app.blueprints
        
        # Check if our blueprint is registered
        assert 'news' in blueprints, "News blueprint is not registered"
        
        # Check if the blueprint has the correct name
        assert blueprints['news'].name == 'news', "Blueprint name is incorrect"
        
        # Check if the index route exists
        url = url_for('news.index')
        assert url == '/news/', "News index URL is incorrect"

def test_news_index_endpoint(client):
    """Test that the news index endpoint returns a successful response."""
    response = client.get('/news/')
    assert response.status_code == 200, "News index endpoint should return 200"

def test_news_market_endpoint(client):
    """Test that the market news endpoint returns a successful response."""
    response = client.get('/news/market')
    assert response.status_code == 200, "Market news endpoint should return 200"
    assert response.is_json, "Response should be JSON"

def test_news_headlines_endpoint(client):
    """Test that the headlines endpoint returns a successful response."""
    response = client.get('/news/headlines')
    assert response.status_code == 200, "Headlines endpoint should return 200"
    assert response.is_json, "Response should be JSON"

def test_news_search_endpoint(client):
    """Test that the news search endpoint returns a successful response."""
    response = client.get('/news/search?q=test')
    assert response.status_code == 200, "News search endpoint should return 200"
    assert response.is_json, "Response should be JSON" 