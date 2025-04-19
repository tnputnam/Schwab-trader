from typing import Dict, Any, Optional
from functools import wraps
from flask import jsonify, render_template, flash
import logging

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base class for application errors."""
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class APIError(AppError):
    """Error class for API-related errors."""
    def __init__(
        self,
        message: str,
        code: str = "API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)

class ValidationError(AppError):
    """Error class for validation errors."""
    def __init__(
        self,
        message: str,
        code: str = "VALIDATION_ERROR",
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, status_code, details)

def handle_errors(f):
    """Decorator to handle errors consistently."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except AppError as e:
            logger.error(f"{e.code}: {e.message}")
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'code': e.code,
                    'message': e.message,
                    'details': e.details
                }), e.status_code
            flash(e.message, 'error')
            return render_template('error.html', error=e), e.status_code
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'code': 'INTERNAL_ERROR',
                    'message': 'An unexpected error occurred',
                    'details': str(e)
                }), 500
            flash('An unexpected error occurred', 'error')
            return render_template('error.html', error=e), 500
    return decorated_function

def validate_request_data(required_fields: list):
    """Decorator to validate request data."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                raise ValidationError('No data provided')
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(
                    f'Missing required fields: {", ".join(missing_fields)}'
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator 