"""Watchlist blueprint for Schwab Trader."""
from flask import Blueprint, render_template
from schwab_trader.utils.auth_decorators import require_schwab_auth

bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@bp.route('/')
@require_schwab_auth
def index():
    """Render the watchlist dashboard."""
    return render_template('watchlist.html') 