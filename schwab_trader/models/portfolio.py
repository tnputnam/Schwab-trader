from datetime import datetime
from schwab_trader.database import db

class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total_value = db.Column(db.Float, nullable=False, default=0.0)
    cash_value = db.Column(db.Float, nullable=False, default=0.0)
    total_gain = db.Column(db.Float, nullable=False, default=0.0)
    total_gain_percent = db.Column(db.Float, nullable=False, default=0.0)
    day_change = db.Column(db.Float, nullable=False, default=0.0)
    day_change_percent = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    positions = db.relationship('Position', backref='portfolio', lazy=True)

    def __repr__(self):
        return f'<Portfolio {self.name}>' 