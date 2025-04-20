import pytest
from flask import url_for
from schwab_trader import create_app

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    return app

def test_analysis_dashboard_blueprint_registration(app):
    """Test that the analysis dashboard blueprint is properly registered."""
    # Get all registered blueprints
    blueprints = app.blueprints
    
    # Check if our blueprint is registered
    assert 'analysis_dashboard' in blueprints, "Analysis dashboard blueprint is not registered"
    
    # Check if the blueprint has the correct name
    assert blueprints['analysis_dashboard'].name == 'analysis_dashboard', "Blueprint name is incorrect"
    
    # Check if the index route exists
    with app.test_request_context():
        # This will raise a BuildError if the endpoint doesn't exist
        url = url_for('analysis_dashboard_bp.index')
        assert url == '/analysis/dashboard/', "URL for analysis dashboard index is incorrect"

def test_analysis_dashboard_endpoint(app):
    """Test that the analysis dashboard endpoint returns a successful response."""
    with app.test_client() as client:
        response = client.get('/analysis/dashboard/')
        assert response.status_code == 200, "Analysis dashboard endpoint did not return 200 OK" 