from flask import Blueprint, render_template, redirect, url_for

bp = Blueprint('root', __name__)

@bp.route('/')
def index():
    return redirect(url_for('dashboard.index')) 