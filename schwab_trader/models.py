"""Database models for the Schwab Trader application."""
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from schwab_trader import db

class User(db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Update the user's last login timestamp."""
        self.last_login = datetime.utcnow()
        db.session.commit()

class Session(db.Model):
    """Session model for managing user sessions."""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('sessions', lazy=True))
    
    def is_expired(self):
        """Check if the session has expired."""
        return datetime.utcnow() > self.expires_at
    
    @classmethod
    def create_session(cls, user_id, duration_hours=24):
        """Create a new session for a user."""
        session = cls(
            user_id=user_id,
            session_token=generate_password_hash(str(user_id) + str(datetime.utcnow())),
            expires_at=datetime.utcnow() + timedelta(hours=duration_hours)
        )
        db.session.add(session)
        db.session.commit()
        return session

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

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    portfolio_id = db.Column(db.Integer, db.ForeignKey('portfolio.id'), nullable=False)
    symbol = db.Column(db.String(10), nullable=False)
    description = db.Column(db.String(200))
    quantity = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_basis = db.Column(db.Float, nullable=False)
    market_value = db.Column(db.Float, nullable=False)
    day_change_dollar = db.Column(db.Float, default=0.0)
    day_change_percent = db.Column(db.Float, default=0.0)
    
    # Additional metrics
    sector = db.Column(db.String(100))
    industry = db.Column(db.String(200))
    security_type = db.Column(db.String(50))
    pe_ratio = db.Column(db.Float)
    market_cap = db.Column(db.Float)
    dividend_yield = db.Column(db.Float)
    eps = db.Column(db.Float)
    beta = db.Column(db.Float)
    volume = db.Column(db.Float)
    avg_volume = db.Column(db.Float)
    
    # Trading metrics
    last_signal = db.Column(db.String(50))
    last_signal_date = db.Column(db.DateTime)
    stop_loss = db.Column(db.Float)
    take_profit = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Position {self.symbol}>'

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