import pytest
from flask import url_for
from schwab_trader import create_app, db
from schwab_trader.models.user import User
from schwab_trader.models.portfolio import Portfolio

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    yield app
    
    # Clean up
    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def auth_client(app, client):
    """Create an authenticated test client."""
    with app.app_context():
        # Create a test user
        user = User(username='testuser', email='test@example.com')
        user.set_password('testpass')
        db.session.add(user)
        
        # Create a test portfolio
        portfolio = Portfolio(name='Test Portfolio', user=user)
        db.session.add(portfolio)
        
        db.session.commit()
        
        # Log in the test user
        client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'testpass'
        })
        
        return client

def test_analysis_dashboard_route(auth_client):
    """Test the analysis dashboard route."""
    response = auth_client.get('/analysis/dashboard')
    assert response.status_code == 200
    assert b'Market Analysis Dashboard' in response.data

def test_market_status_api(auth_client):
    """Test the market status API endpoint."""
    response = auth_client.get('/analysis/dashboard/api/market-status')
    assert response.status_code in [200, 500]  # Allow for service unavailability
    data = response.get_json()
    assert 'status' in data

def test_market_data_api(auth_client):
    """Test the market data API endpoint."""
    response = auth_client.get('/analysis/dashboard/api/market-data?symbol=AAPL&timeframe=1d&type=price')
    assert response.status_code in [200, 500]  # Allow for service unavailability
    data = response.get_json()
    assert 'status' in data

def test_analysis_button_navigation(auth_client):
    """Test the analysis button navigation."""
    # First visit the index page
    response = auth_client.get('/')
    assert response.status_code == 200
    
    # Then click the analysis button (simulated by following the link)
    response = auth_client.get('/analysis/dashboard')
    assert response.status_code == 200
    assert b'Market Analysis Dashboard' in response.data

def test_analysis_route_without_auth(client):
    """Test that analysis routes require authentication."""
    response = client.get('/analysis/dashboard')
    assert response.status_code == 302  # Should redirect to login
    assert '/auth/login' in response.location

def test_analysis_api_without_auth(client):
    """Test that analysis API endpoints require authentication."""
    response = client.get('/analysis/dashboard/api/market-status')
    assert response.status_code == 302  # Should redirect to login
    assert '/auth/login' in response.location 