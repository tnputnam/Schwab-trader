import pytest
from datetime import datetime
from schwab_trader import create_app, db
from schwab_trader.models.models import User, Portfolio, Strategy, Position, Trade
from schwab_trader.routes import auth, news, strategies
from schwab_trader.utils.logger import db_logger
import uuid

@pytest.fixture
def test_user(session):
    """Create a test user."""
    user = User(
        username='testuser',
        email='test@example.com',
        password='testpass'
    )
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def test_portfolio(session, test_user):
    """Create a test portfolio."""
    portfolio = Portfolio(
        name='Test Portfolio',
        user_id=test_user.id
    )
    session.add(portfolio)
    session.commit()
    return portfolio

@pytest.fixture
def test_strategy(session, test_portfolio):
    """Create a test strategy."""
    strategy = Strategy(
        name='Test Strategy',
        portfolio_id=test_portfolio.id,
        type='momentum',
        parameters={'lookback': 20}
    )
    session.add(strategy)
    session.commit()
    return strategy

def test_user_creation(session, test_user):
    """Test user creation."""
    assert test_user.id is not None
    assert test_user.username == 'testuser'
    assert test_user.email == 'test@example.com'

def test_portfolio_creation(session, test_portfolio, test_user):
    """Test portfolio creation."""
    assert test_portfolio.id is not None
    assert test_portfolio.name == 'Test Portfolio'
    assert test_portfolio.user_id == test_user.id

def test_strategy_creation(session, test_strategy, test_portfolio):
    """Test strategy creation."""
    assert test_strategy.id is not None
    assert test_strategy.name == 'Test Strategy'
    assert test_strategy.portfolio_id == test_portfolio.id
    assert test_strategy.type == 'momentum'
    assert test_strategy.parameters == {'lookback': 20}

def test_portfolio_operations(session, test_user, test_portfolio):
    """Test portfolio operations"""
    # Test portfolio creation
    assert test_portfolio.name.startswith('Test Portfolio')
    assert test_portfolio.user_id == test_user.id
    
    # Test portfolio update
    test_portfolio.current_value = 11000.00
    session.commit()
    updated_portfolio = session.get(Portfolio, test_portfolio.id)
    assert updated_portfolio.current_value == 11000.00

def test_position_operations(session, test_portfolio, test_strategy):
    """Test position operations"""
    # Create a position
    position = Position(
        portfolio_id=test_portfolio.id,
        symbol='AAPL',
        quantity=100,
        entry_price=150.00,
        current_price=160.00,
        entry_date=datetime.utcnow(),
        strategy_id=test_strategy.id
    )
    session.add(position)
    session.commit()
    
    # Test position creation
    assert position.symbol == 'AAPL'
    assert position.quantity == 100
    assert position.strategy_id == test_strategy.id

def test_trade_operations(session, test_portfolio, test_strategy):
    """Test trade operations"""
    # Create a trade
    trade = Trade(
        portfolio_id=test_portfolio.id,
        symbol='AAPL',
        type='BUY',
        quantity=100,
        price=150.00,
        timestamp=datetime.utcnow(),
        strategy_id=test_strategy.id
    )
    session.add(trade)
    session.commit()
    
    # Test trade creation
    assert trade.symbol == 'AAPL'
    assert trade.type == 'BUY'
    assert trade.quantity == 100
    assert trade.strategy_id == test_strategy.id

def test_strategy_operations(session, test_strategy):
    """Test strategy operations"""
    # Test strategy creation
    assert test_strategy.name == 'Test Strategy'
    assert test_strategy.type == 'momentum'
    assert test_strategy.parameters == {'lookback': 20}
    
    # Test strategy update
    test_strategy.parameters = {'lookback': 40}
    session.commit()
    updated_strategy = session.get(Strategy, test_strategy.id)
    assert updated_strategy.parameters == {'lookback': 40}
