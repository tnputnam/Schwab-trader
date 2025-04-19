"""Alerts blueprint for Schwab Trader."""
from flask import Blueprint, render_template
from schwab_trader.utils.auth_decorators import require_schwab_auth

bp = Blueprint('alerts', __name__, url_prefix='/alerts')

@bp.route('/')
@require_schwab_auth
def index():
    """Render the alerts dashboard."""
    return render_template('alerts.html') 