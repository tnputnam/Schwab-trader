"""Position model for Schwab Trader."""
from datetime import datetime
from schwab_trader.models.user import db

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
    
    def __repr__(self):
        return f'<Position {self.symbol} {self.quantity}>'
    
    def to_dict(self):
        """Convert position to dictionary."""
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'symbol': self.symbol,
            'quantity': self.quantity,
            'price': self.price,
            'cost_basis': self.cost_basis,
            'sector': self.sector,
            'industry': self.industry,
            'pe_ratio': self.pe_ratio,
            'market_cap': self.market_cap,
            'dividend_yield': self.dividend_yield,
            'eps': self.eps,
            'beta': self.beta,
            'volume': self.volume,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 