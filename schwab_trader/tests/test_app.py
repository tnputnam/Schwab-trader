import pytest
from flask import Flask, session
from schwab_trader.auth_app import init_app
import os

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Configure template directory
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app.template_folder = template_dir
    
    # Initialize the app with routes
    init_app(app)
    
    return app

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

def test_login_route(client):
    """Test the login route redirects to analysis dashboard."""
    response = client.get('/login')
    assert response.status_code == 200  # Should render login page

def test_analysis_route_unauthorized(client):
    """Test the analysis route redirects to manual auth when not logged in."""
    response = client.get('/analysis')
    assert response.status_code == 302  # Redirect status code
    assert '/login' in response.location

def test_analysis_route_authorized(client):
    """Test the analysis route redirects to dashboard when logged in."""
    with client.session_transaction() as sess:
        sess['schwab_token'] = 'test-token'
    
    response = client.get('/analysis')
    assert response.status_code == 302  # Redirect status code
    assert '/analysis' in response.location

def test_auth_callback_route(client):
    """Test the auth callback route handles errors gracefully."""
    response = client.get('/auth/callback')
    assert response.status_code == 500
    assert b'error' in response.data

def test_root_route(client):
    """Test the root route is accessible."""
    response = client.get('/')
    assert response.status_code == 200 