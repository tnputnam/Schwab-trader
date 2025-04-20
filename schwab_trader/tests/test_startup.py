"""Test the application startup and configuration."""
import os
import pytest
from schwab_trader import create_app
from schwab_trader.utils.error_handling import setup_logging

def test_create_app():
    """Test that the application can be created with test configuration."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SCHWAB_CLIENT_ID': 'test-client-id',
        'SCHWAB_CLIENT_SECRET': 'test-client-secret',
        'SCHWAB_REDIRECT_URI': 'http://localhost:5000/auth/callback'
    })
    assert app is not None
    assert app.config['TESTING'] is True
    assert app.config['SECRET_KEY'] == 'test-key'

def test_app_context():
    """Test that the application context works."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'
    })
    with app.app_context():
        assert app.config['TESTING'] is True

def test_logging_setup():
    """Test that logging can be set up."""
    app = create_app({
        'TESTING': True,
        'SECRET_KEY': 'test-key'
    })
    with app.app_context():
        setup_logging(app)
        assert app.logger is not None
        assert app.logger.level == 20  # INFO level 