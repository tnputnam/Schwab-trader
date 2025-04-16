"""Models for Schwab Trader."""
from schwab_trader.database import db
from datetime import datetime

class Portfolio(db.Model):
    """Portfolio model."""
    
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    positions = db.relationship('Position', backref='portfolio', lazy=True)
    trades = db.relationship('Trade', backref='portfolio', lazy=True)

class Position(db.Model):
    """Position model."""
    
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float, nullable=False)
    sector = db.Column(db.String(50))
    industry = db.Column(db.String(50))
    pe_ratio = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    dividend_yield = db.Column(db.Float)
    eps = db.Column(db.Float)
    beta = db.Column(db.Float)
    volume = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Trade(db.Model):
    """Trade model."""
    
    __tablename__ = 'trades'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(4), nullable=False)  # BUY or SELL
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    strategy = db.Column(db.String(50))  # Name of the strategy that generated the trade
    reason = db.Column(db.String(200))  # Reason for the trade

# Import User model
from .user import User

# Export models
__all__ = ['Portfolio', 'Position', 'Trade', 'User'] 