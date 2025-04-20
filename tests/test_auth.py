import pytest
from flask import url_for
from schwab_trader.models import User

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