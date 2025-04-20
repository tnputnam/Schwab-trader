import pytest
from flask import url_for
from schwab_trader import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    test_config = {
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'SECRET_KEY': 'test'
    }
    app = create_app(test_config)
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_analysis_dashboard_blueprint_registration(app):
    """Test that the analysis dashboard blueprint is properly registered."""
    with app.app_context():
        # Get all registered blueprints
        blueprints = app.blueprints
        
        # Check if our blueprint is registered
        assert 'analysis_dashboard' in blueprints, "Analysis dashboard blueprint is not registered"
        
        # Check if the blueprint has the correct name
        assert blueprints['analysis_dashboard'].name == 'analysis_dashboard', "Blueprint name is incorrect"
        
        # Check if the index route exists
        url = url_for('analysis_dashboard_bp.index')
        assert url == '/analysis/dashboard/', "URL for analysis dashboard index is incorrect"

def test_analysis_dashboard_endpoint(client):
    """Test that the analysis dashboard endpoint returns a successful response."""
    response = client.get('/analysis/dashboard/')
    assert response.status_code == 200, "Analysis dashboard endpoint did not return 200 OK" 