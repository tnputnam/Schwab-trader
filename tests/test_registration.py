import pytest
from flask import url_for
from schwab_trader.models import User

def test_registration_success(client, session):
    """Test successful user registration."""
    response = client.post(url_for('auth.register'), data={
        'username': 'newuser',
        'password': 'newpass123',
        'password_confirm': 'newpass123'
    })
    assert response.status_code == 200
    assert b'Registration successful' in response.data
    
    user = session.query(User).filter_by(username='newuser').first()
    assert user is not None
    assert user.username == 'newuser'

def test_registration_duplicate_username(client, test_user):
    """Test registration with duplicate username."""
    response = client.post(url_for('auth.register'), data={
        'username': 'testuser',
        'password': 'newpass123',
        'password_confirm': 'newpass123'
    })
    assert response.status_code == 400
    assert b'Username already exists' in response.data

def test_registration_password_mismatch(client):
    """Test registration with mismatched passwords."""
    response = client.post(url_for('auth.register'), data={
        'username': 'newuser',
        'password': 'pass1',
        'password_confirm': 'pass2'
    })
    assert response.status_code == 400
    assert b'Passwords must match' in response.data

def test_registration_form_validation(client):
    """Test registration form validation."""
    response = client.post(url_for('auth.register'), data={})
    assert response.status_code == 400
    assert b'Username is required' in response.data
    assert b'Password is required' in response.data 