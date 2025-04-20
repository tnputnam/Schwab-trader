"""Test the Flask application."""
import pytest
from flask import Flask, url_for
from schwab_trader import create_app
import os

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SCHWAB_CLIENT_ID': 'test-client-id',
        'SCHWAB_CLIENT_SECRET': 'test-client-secret',
        'SCHWAB_REDIRECT_URI': 'http://localhost:5000/auth/callback',
        'SCHWAB_AUTH_URL': 'https://test-auth-url',
        'SCHWAB_TOKEN_URL': 'https://test-token-url',
        'SCHWAB_API_BASE_URL': 'https://test-api-url'
    })
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    
    # Configure template directory
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    app.template_folder = template_dir
    
    return app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

def test_root_route(client):
    """Test the root route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Schwab Trader' in response.data

def test_login_route(client):
    """Test the login route."""
    response = client.get('/auth/login')
    assert response.status_code == 405  # Method Not Allowed since it's POST only
    response = client.post('/auth/login')
    assert response.status_code == 200

def test_auth_callback_route(client):
    """Test the auth callback route handles errors gracefully."""
    response = client.get('/auth/callback')
    assert response.status_code == 500
    assert b'error' in response.data

def test_analysis_route_unauthorized(client):
    """Test the analysis route redirects to login when not authorized."""
    response = client.get('/analysis')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location']

def test_analysis_route_authorized(client):
    """Test the analysis route is accessible when authorized."""
    with client.session_transaction() as sess:
        sess['schwab_token'] = 'test-token'
    
    response = client.get('/analysis')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location']

def test_portfolio_route_unauthorized(client):
    """Test the portfolio route redirects to login when not authorized."""
    response = client.get('/portfolio')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location']

def test_trading_route_unauthorized(client):
    """Test the trading route redirects to login when not authorized."""
    response = client.get('/trading')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location']

def test_news_route_unauthorized(client):
    """Test the news route redirects to login when not authorized."""
    response = client.get('/news')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location']

def test_strategies_route_unauthorized(client):
    """Test the strategies route redirects to login when not authorized."""
    response = client.get('/strategies')
    assert response.status_code == 308  # Permanent Redirect
    assert '/auth/login' in response.headers['Location'] 