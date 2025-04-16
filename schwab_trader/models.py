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
    last_price = db.Column(db.Float, nullable=False)
    avg_cost = db.Column(db.Float, nullable=False)
    market_value = db.Column(db.Float, nullable=False)
    day_change_dollar = db.Column(db.Float, nullable=False)
    day_change_percent = db.Column(db.Float, nullable=False) 