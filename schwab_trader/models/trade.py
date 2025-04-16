from datetime import datetime
from schwab_trader.database import db

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    action = db.Column(db.String(10), nullable=False)  # BUY, SELL
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    total_value = db.Column(db.Float, nullable=False)
    strategy_name = db.Column(db.String(100))
    reason = db.Column(db.String(200))
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Trade {self.action} {self.symbol}>' 