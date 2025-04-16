import os
import sys
from datetime import datetime

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)

from schwab_trader import create_app
from schwab_trader.models import db, Portfolio, Position

def display_portfolio():
    """Display portfolio data from database"""
    try:
        app = create_app()
        with app.app_context():
            # Get the portfolio
            portfolio = Portfolio.query.filter_by(name='Schwab Portfolio').first()
            if not portfolio:
                print("No portfolio found!")
                return
            
            # Get all positions
            positions = Position.query.filter_by(portfolio_id=portfolio.id).all()
            
            # Calculate totals
            total_value = sum(p.market_value for p in positions)
            total_cost = sum(p.cost_basis for p in positions)
            total_gain = total_value - total_cost
            total_gain_pct = (total_gain / total_cost * 100) if total_cost > 0 else 0
            total_day_change = sum(p.day_change_dollar for p in positions)
            
            # Display portfolio summary
            print("\n=== Portfolio Summary ===")
            print(f"Total Market Value: ${total_value:,.2f}")
            print(f"Total Cost Basis: ${total_cost:,.2f}")
            print(f"Total Gain/Loss: ${total_gain:,.2f} ({total_gain_pct:.2f}%)")
            print(f"Day Change: ${total_day_change:,.2f}")
            
            # Display positions
            print("\n=== Positions ===")
            print(f"{'Symbol':<10} {'Quantity':>10} {'Price':>12} {'Market Value':>15} {'Day Change':>12} {'Day Change %':>12} {'Type':<10}")
            print("-" * 85)
            
            for pos in positions:
                print(f"{pos.symbol:<10} {pos.quantity:>10,.2f} ${pos.price:>10,.2f} ${pos.market_value:>13,.2f} ${pos.day_change_dollar:>10,.2f} {pos.day_change_percent:>11.2f}% {pos.security_type:<10}")
                
    except Exception as e:
        print(f"Error displaying portfolio: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    display_portfolio() 