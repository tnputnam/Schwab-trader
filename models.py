from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

class Portfolio(Base):
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    total_value = Column(Float, default=0.0)
    cash_balance = Column(Float, default=0.0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    positions = relationship("Position", back_populates="portfolio")
    trades = relationship("Trade", back_populates="portfolio")
    watchlist_items = relationship("WatchlistItem", back_populates="portfolio")
    alerts = relationship("Alert", back_populates="portfolio")

class Position(Base):
    __tablename__ = 'positions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String)
    quantity = Column(Float)
    average_price = Column(Float)
    current_price = Column(Float)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    portfolio = relationship("Portfolio", back_populates="positions")

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String)
    quantity = Column(Float)
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    action = Column(String)  # 'buy' or 'sell'
    
    portfolio = relationship("Portfolio", back_populates="trades")

class WatchlistItem(Base):
    __tablename__ = 'watchlist_items'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String)
    added_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(String, nullable=True)
    
    portfolio = relationship("Portfolio", back_populates="watchlist_items")

class Alert(Base):
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    symbol = Column(String)
    condition_type = Column(String)  # 'price_above', 'price_below', 'percent_change'
    threshold = Column(Float)
    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    last_triggered = Column(DateTime, nullable=True)
    
    portfolio = relationship("Portfolio", back_populates="alerts")

class PortfolioHistory(Base):
    __tablename__ = 'portfolio_history'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'))
    timestamp = Column(DateTime, default=datetime.utcnow)
    total_value = Column(Float)
    cash_balance = Column(Float)

# Create database engine
engine = create_engine('sqlite:///trading.db')

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
SessionLocal = sessionmaker(bind=engine)

# Function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 