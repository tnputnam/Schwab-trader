"""Portfolio model for Schwab Trader."""
from datetime import datetime
from schwab_trader.models import db

class Portfolio(db.Model):
    """Portfolio model."""
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    description = db.Column(db.String(200))
    total_value = db.Column(db.Float, nullable=False, default=0.0)
    cash_value = db.Column(db.Float, nullable=False, default=0.0)
    total_gain = db.Column(db.Float, nullable=False, default=0.0)
    total_gain_percent = db.Column(db.Float, nullable=False, default=0.0)
    day_change = db.Column(db.Float, nullable=False, default=0.0)
    day_change_percent = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('portfolios', lazy=True))
    positions = db.relationship('Position', backref='portfolio', lazy=True)
    
    def __init__(self, name, user):
        """Initialize portfolio."""
        self.name = name
        self.user = user
    
    def __repr__(self):
        """Represent portfolio as string."""
        return f'<Portfolio {self.name}>'
    
    def to_dict(self):
        """Convert portfolio to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'positions': [position.to_dict() for position in self.positions]
        } 