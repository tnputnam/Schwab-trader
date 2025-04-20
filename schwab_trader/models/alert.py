"""Alert model for Schwab Trader."""
from datetime import datetime
from schwab_trader.models.user import db

class Alert(db.Model):
    """Alert model."""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    alert_type = db.Column(db.String(20), nullable=False)  # price, volume, technical
    condition = db.Column(db.String(20), nullable=False)  # above, below, crosses
    value = db.Column(db.Float, nullable=False)
    active = db.Column(db.Boolean, default=True)
    triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Alert {self.symbol} {self.alert_type} {self.condition} {self.value}>'
    
    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'symbol': self.symbol,
            'alert_type': self.alert_type,
            'condition': self.condition,
            'value': self.value,
            'active': self.active,
            'triggered': self.triggered,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 