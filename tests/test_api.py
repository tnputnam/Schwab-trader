import pytest
from unittest.mock import patch, MagicMock
from flask import url_for
from schwab_trader import create_app, db
from schwab_trader.models.models import User, Portfolio, Strategy
from schwab_trader.utils.cache import Cache
from schwab_trader.utils.logger import api_logger
from schwab_trader.utils.error_handler import APIError
import uuid

@pytest.fixture
def test_user(session):
    """Create a test user with unique email"""
    unique_id = str(uuid.uuid4())
    user = User(
        username=f'test_user_{unique_id}',
        email=f'test_{unique_id}@example.com'
    )
    user.set_password('password123')
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def mock_redis():
    """Mock Redis client"""
    with patch('redis.Redis') as mock:
        redis_client = MagicMock()
        mock.return_value = redis_client
        yield redis_client

@pytest.fixture
def mock_news_api():
    """Mock the news API responses"""
    with patch('schwab_trader.services.news.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'status': 'ok',
            'articles': [
                {
                    'title': 'Test News',
                    'description': 'Test Description',
                    'url': 'http://test.com',
                    'publishedAt': '2024-01-01T00:00:00Z'
                }
            ]
        }
        yield mock_get

@pytest.fixture
def mock_alpha_vantage():
    """Mock the Alpha Vantage API responses"""
    with patch('schwab_trader.services.alpha_vantage.requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            'Global Quote': {
                '01. symbol': 'AAPL',
                '02. open': '150.00',
                '03. high': '155.00',
                '04. low': '148.00',
                '05. price': '152.00',
                '06. volume': '1000000',
                '07. latest trading day': '2024-01-01',
                '08. previous close': '149.00',
                '09. change': '3.00',
                '10. change percent': '2.01%'
            }
        }
        yield mock_get

def test_news_api(client, mock_news_api):
    """Test news API endpoints"""
    # Test market news endpoint
    response = client.get('/api/news/market')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['articles']) == 1
    assert data['articles'][0]['title'] == 'Test News'
    
    # Test headlines endpoint
    response = client.get('/api/news/headlines')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(data['articles']) == 1

def test_trading_api(client, test_user, mock_alpha_vantage):
    """Test trading API endpoints"""
    # Login the test user
    with client.session_transaction() as session:
        session['user_id'] = test_user.id
    
    # Test stock quote endpoint
    response = client.get('/api/trading/quote/AAPL')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['symbol'] == 'AAPL'
    assert data['price'] == '152.00'
    
    # Test backtesting endpoint
    response = client.post('/api/trading/backtest', json={
        'symbol': 'AAPL',
        'strategy': 'MA',
        'start_date': '2023-01-01',
        'end_date': '2024-01-01'
    })
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'results' in data

def test_cache(client, mock_redis):
    """Test cache functionality"""
    # Test setting cache
    response = client.post('/api/cache/set', json={
        'key': 'test_key',
        'value': 'test_value',
        'expire': 60
    })
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    
    # Verify Redis setex was called
    mock_redis.setex.assert_called_once_with(
        'test_key',
        60,
        '"test_value"'
    )
    
    # Test getting cache
    mock_redis.get.return_value = '"test_value"'
    response = client.get('/api/cache/get/test_key')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    assert response.json['value'] == 'test_value'
    
    # Test deleting cache
    response = client.delete('/api/cache/delete/test_key')
    assert response.status_code == 200
    assert response.json['status'] == 'success'
    mock_redis.delete.assert_called_once_with('test_key')

def test_error_handling(client):
    """Test error handling"""
    # Test invalid API key
    with patch('schwab_trader.services.news.requests.get') as mock_get:
        mock_get.side_effect = APIError('Invalid API key', status_code=400)
        response = client.get('/api/news/market')
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'Invalid API key' in data['message']
    
    # Test rate limit error
    with patch('schwab_trader.services.alpha_vantage.requests.get') as mock_get:
        mock_get.side_effect = APIError('Rate limit exceeded', status_code=429)
        response = client.get('/api/trading/quote/AAPL')
        assert response.status_code == 429
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'rate limit' in data['message'].lower()
