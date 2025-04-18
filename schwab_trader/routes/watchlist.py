"""Watchlist blueprint for Schwab Trader."""
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('watchlist', __name__, url_prefix='/watchlist')

@bp.route('/')
def index():
    """Render the watchlist dashboard."""
    if 'schwab_token' not in session:
        return redirect(url_for('root.login'))
    return render_template('watchlist.html') 