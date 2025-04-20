import pytest
from flask import url_for, session
from schwab_trader.models import User
from schwab_trader.services.market_data_service import MarketDataService

def test_login_success(client, test_user):
    """Test successful login."""
    response = client.post(url_for('auth.login'), data={
        'username': 'testuser',
        'password': 'testpass',
        'remember_me': False
    })
    assert response.status_code == 200
    assert b'Login successful' in response.data

def test_login_invalid_username(client, test_user):
    """Test login with invalid username."""
    response = client.post(url_for('auth.login'), data={
        'username': 'wronguser',
        'password': 'testpass',
        'remember_me': False
    })
    assert response.status_code == 401
    assert b'Invalid username or password' in response.data

def test_login_invalid_password(client, test_user):
    """Test login with invalid password."""
    response = client.post(url_for('auth.login'), data={
        'username': 'testuser',
        'password': 'wrongpass',
        'remember_me': False
    })
    assert response.status_code == 401
    assert b'Invalid username or password' in response.data

def test_login_form_validation(client):
    """Test login form validation."""
    response = client.post(url_for('auth.login'), data={})
    assert response.status_code == 400
    assert b'Username is required' in response.data
    assert b'Password is required' in response.data

def test_bypass_status_get(client):
    """Test getting the bypass status."""
    response = client.get('/auth/bypass')
    assert response.status_code == 200
    data = response.get_json()
    assert 'status' in data
    assert 'bypassed' in data
    assert data['status'] == 'success'
    assert data['bypassed'] is False

def test_bypass_toggle_on(client):
    """Test enabling the bypass."""
    response = client.post('/auth/bypass', json={'bypass': True})
    assert response.status_code == 302  # Should redirect to Schwab auth
    assert 'schwab_bypassed' in session
    assert session['schwab_bypassed'] is True

def test_bypass_toggle_off(client):
    """Test disabling the bypass."""
    # First enable bypass
    client.post('/auth/bypass', json={'bypass': True})
    
    # Then disable it
    response = client.post('/auth/bypass', json={'bypass': False})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['bypassed'] is False
    assert 'schwab_bypassed' in session
    assert session['schwab_bypassed'] is False

def test_force_bypass_off(client):
    """Test forcing bypass off."""
    # First enable bypass
    client.post('/auth/bypass', json={'bypass': True})
    
    # Then force it off
    response = client.post('/auth/force_bypass_off')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['bypassed'] is False
    assert 'schwab_bypassed' in session
    assert session['schwab_bypassed'] is False

def test_bypass_with_invalid_data(client):
    """Test bypass with invalid data."""
    response = client.post('/auth/bypass', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['bypassed'] is False

def test_bypass_with_market_data_service_error(client, monkeypatch):
    """Test bypass when market data service fails."""
    def mock_toggle_bypass(*args, **kwargs):
        raise Exception("Test error")
    
    monkeypatch.setattr(MarketDataService, 'toggle_bypass', mock_toggle_bypass)
    
    response = client.post('/auth/bypass', json={'bypass': True})
    assert response.status_code == 500
    data = response.get_json()
    assert data['status'] == 'error'
    assert 'message' in data 