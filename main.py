from fastapi import FastAPI, Request, WebSocket, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import yfinance as yf
from datetime import datetime, timedelta
import os
import requests
from dotenv import load_dotenv
import json
import asyncio
from typing import List
from sqlalchemy.orm import Session
import models
from models import get_db

# Load environment variables
load_dotenv()

app = FastAPI(title="Schwab Trader")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Alpha Vantage API key
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/trading", response_class=HTMLResponse)
async def trading(request: Request):
    return templates.TemplateResponse("trading.html", {"request": request})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Parse the received data
            try:
                message = json.loads(data)
                if message.get("type") == "subscribe":
                    # Handle symbol subscription
                    symbols = message.get("symbols", [])
                    # Start monitoring these symbols
                    asyncio.create_task(monitor_symbols(symbols))
            except json.JSONDecodeError:
                pass
    except:
        manager.disconnect(websocket)

async def monitor_symbols(symbols: List[str]):
    while True:
        try:
            quotes = {}
            for symbol in symbols:
                if ALPHA_VANTAGE_API_KEY:
                    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
                    response = requests.get(url)
                    data = response.json()
                    if "Global Quote" in data:
                        quote = data["Global Quote"]
                        quotes[symbol] = {
                            "price": float(quote["05. price"]),
                            "change": float(quote["09. change"]),
                            "change_percent": float(quote["10. change percent"].replace("%", ""))
                        }
            
            if quotes:
                await manager.broadcast(json.dumps({
                    "type": "quotes",
                    "data": quotes
                }))
        except Exception as e:
            print(f"Error monitoring symbols: {str(e)}")
        
        # Wait for 5 seconds before next update
        await asyncio.sleep(5)

@app.get("/api/portfolio")
async def get_portfolio(db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).first()
    if not portfolio:
        portfolio = models.Portfolio(total_value=100000.0, cash_balance=100000.0)
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
    
    return {
        "total_value": portfolio.total_value,
        "cash_balance": portfolio.cash_balance,
        "positions": [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "average_price": pos.average_price,
                "current_price": pos.current_price,
                "value": pos.quantity * pos.current_price
            }
            for pos in portfolio.positions
        ],
        "recent_trades": [
            {
                "symbol": trade.symbol,
                "quantity": trade.quantity,
                "price": trade.price,
                "action": trade.action,
                "timestamp": trade.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            }
            for trade in portfolio.trades[-10:]  # Last 10 trades
        ],
        "history": [
            {
                "timestamp": hist.timestamp.strftime("%Y-%m-%d"),
                "total_value": hist.total_value
            }
            for hist in db.query(models.PortfolioHistory)
            .filter_by(portfolio_id=portfolio.id)
            .order_by(models.PortfolioHistory.timestamp.desc())
            .limit(30)
        ]
    }

@app.post("/api/trade")
async def execute_trade(symbol: str, quantity: float, action: str, db: Session = Depends(get_db)):
    try:
        portfolio = db.query(models.Portfolio).first()
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        # Get current price
        stock = yf.Ticker(symbol)
        current_price = stock.info.get('regularMarketPrice', 0)
        
        if action == "buy":
            cost = current_price * quantity
            if cost > portfolio.cash_balance:
                raise HTTPException(status_code=400, detail="Insufficient funds")
            
            # Update position
            position = db.query(models.Position).filter_by(
                portfolio_id=portfolio.id, symbol=symbol
            ).first()
            
            if position:
                # Update existing position
                total_cost = (position.average_price * position.quantity) + cost
                position.quantity += quantity
                position.average_price = total_cost / position.quantity
                position.current_price = current_price
            else:
                # Create new position
                position = models.Position(
                    portfolio_id=portfolio.id,
                    symbol=symbol,
                    quantity=quantity,
                    average_price=current_price,
                    current_price=current_price
                )
                db.add(position)
            
            portfolio.cash_balance -= cost
            
        else:  # sell
            position = db.query(models.Position).filter_by(
                portfolio_id=portfolio.id, symbol=symbol
            ).first()
            
            if not position or position.quantity < quantity:
                raise HTTPException(status_code=400, detail="Insufficient shares")
            
            proceeds = current_price * quantity
            position.quantity -= quantity
            
            if position.quantity == 0:
                db.delete(position)
            
            portfolio.cash_balance += proceeds
        
        # Record trade
        trade = models.Trade(
            portfolio_id=portfolio.id,
            symbol=symbol,
            quantity=quantity,
            price=current_price,
            action=action
        )
        db.add(trade)
        
        # Update portfolio value
        portfolio.total_value = portfolio.cash_balance + sum(
            p.quantity * p.current_price for p in portfolio.positions
        )
        portfolio.last_updated = datetime.utcnow()
        
        # Record portfolio history
        history = models.PortfolioHistory(
            portfolio_id=portfolio.id,
            total_value=portfolio.total_value,
            cash_balance=portfolio.cash_balance
        )
        db.add(history)
        
        db.commit()
        
        # Broadcast update via WebSocket
        await manager.broadcast(json.dumps({
            "type": "trade",
            "data": {
                "symbol": symbol,
                "quantity": quantity,
                "price": current_price,
                "action": action,
                "timestamp": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            }
        }))
        
        return {
            "message": f"Successfully {action}ed {quantity} shares of {symbol} at ${current_price:.2f}",
            "trade_id": trade.id
        }
    
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist")
async def add_to_watchlist(symbol: str, notes: str = None, db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    # Check if already in watchlist
    existing = db.query(models.WatchlistItem).filter_by(
        portfolio_id=portfolio.id, symbol=symbol
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Symbol already in watchlist")
    
    # Add to watchlist
    item = models.WatchlistItem(
        portfolio_id=portfolio.id,
        symbol=symbol,
        notes=notes
    )
    db.add(item)
    db.commit()
    
    return {"message": f"Added {symbol} to watchlist"}

@app.get("/api/watchlist")
async def get_watchlist(db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "items": [
            {
                "symbol": item.symbol,
                "notes": item.notes,
                "added_date": item.added_date.strftime("%Y-%m-%d")
            }
            for item in portfolio.watchlist_items
        ]
    }

@app.post("/api/alerts")
async def create_alert(
    symbol: str,
    condition_type: str,
    threshold: float,
    db: Session = Depends(get_db)
):
    portfolio = db.query(models.Portfolio).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    alert = models.Alert(
        portfolio_id=portfolio.id,
        symbol=symbol,
        condition_type=condition_type,
        threshold=threshold
    )
    db.add(alert)
    db.commit()
    
    return {"message": f"Alert created for {symbol}"}

@app.get("/api/alerts")
async def get_alerts(db: Session = Depends(get_db)):
    portfolio = db.query(models.Portfolio).first()
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    
    return {
        "alerts": [
            {
                "symbol": alert.symbol,
                "condition_type": alert.condition_type,
                "threshold": alert.threshold,
                "is_active": alert.is_active,
                "last_triggered": alert.last_triggered.strftime("%Y-%m-%d %H:%M:%S") if alert.last_triggered else None
            }
            for alert in portfolio.alerts
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 