from flask import Blueprint, render_template

# Initialize blueprint
views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def index():
    """Index page route"""
    return render_template('index.html')