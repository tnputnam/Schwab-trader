"""User model for Schwab Trader."""
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from schwab_trader.database import db

class User(UserMixin, db.Model):
    """User model for authentication."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_active = db.Column(db.Boolean, default=True)
    
    def __init__(self, username, email):
        """Initialize a new user."""
        self.username = username
        self.email = email
    
    def set_password(self, password):
        """Set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        """Return string representation of the user."""
        return f'<User {self.username}>' 