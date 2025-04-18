"""Alerts blueprint for Schwab Trader."""
from flask import Blueprint, render_template, session, redirect, url_for

bp = Blueprint('alerts', __name__, url_prefix='/alerts')

@bp.route('/')
def index():
    """Render the alerts dashboard."""
    if 'schwab_token' not in session:
        return redirect(url_for('root.login'))
    return render_template('alerts.html') 