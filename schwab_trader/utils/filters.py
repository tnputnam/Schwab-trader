"""Custom Jinja2 filters."""

def format_number(value):
    """Format a number with commas as thousand separators."""
    try:
        return "{:,}".format(int(value))
    except (ValueError, TypeError):
        return value

def register_filters(app):
    """Register custom filters with the Flask app."""
    app.jinja_env.filters['format_number'] = format_number 