from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Portfolio(db.Model):
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    positions = db.relationship('Position', backref='portfolio', lazy=True)

class Position(db.Model):
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolios.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    market_value = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float)
    day_change_dollar = db.Column(db.Float)
    day_change_percent = db.Column(db.Float)
    security_type = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Position {self.symbol} ({self.quantity} shares)>' 