from datetime import datetime
from schwab_trader import db

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    total_value = db.Column(db.Float, nullable=False)
    total_change = db.Column(db.Float, nullable=False)
    total_change_percent = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    positions = db.relationship('Position', backref='portfolio', lazy=True)

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(200))
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float, nullable=False)
    market_value = db.Column(db.Float, nullable=False)
    day_change_dollar = db.Column(db.Float)
    day_change_percent = db.Column(db.Float)
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(200))
    pe_ratio = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    dividend_yield = db.Column(db.Float)
    eps = db.Column(db.Float)
    beta = db.Column(db.Float)
    volume = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Position {self.symbol}>' 