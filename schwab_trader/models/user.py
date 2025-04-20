"""User model for Schwab Trader."""
from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from schwab_trader.utils.error_utils import DatabaseError
from schwab_trader.utils.logging_utils import get_logger

logger = get_logger(__name__)
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120))
    access_token = db.Column(db.String(512))
    refresh_token = db.Column(db.String(512))
    token_expires_at = db.Column(db.DateTime)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_or_create(cls, email: str, name: str) -> 'User':
        """Get or create a user."""
        try:
            user = cls.query.filter_by(email=email).first()
            if not user:
                user = cls(email=email, name=name)
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new user: {email}")
            return user
        except Exception as e:
            logger.error(f"Error getting/creating user: {str(e)}")
            raise DatabaseError(details=str(e))
    
    def update_tokens(self, tokens: dict) -> None:
        """Update user tokens."""
        try:
            self.access_token = tokens['access_token']
            self.refresh_token = tokens['refresh_token']
            self.token_expires_at = tokens['expires_at']
            db.session.commit()
            logger.info(f"Updated tokens for user: {self.email}")
        except Exception as e:
            logger.error(f"Error updating tokens: {str(e)}")
            raise DatabaseError(details=str(e))
    
    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.token_expires_at:
            return True
        return datetime.utcnow() >= self.token_expires_at
    
    def to_dict(self) -> dict:
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 