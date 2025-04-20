"""Centralized error handling utilities for Schwab Trader."""
from typing import Dict, Any, Optional, Union, Callable
from functools import wraps
from flask import jsonify, render_template, flash, current_app, request
import logging
from werkzeug.exceptions import HTTPException
import traceback
from .logging_utils import get_logger

logger = get_logger(__name__)

class AppError(Exception):
    """Base exception class for application errors."""
    def __init__(self, message: str, status_code: int = 400, code: str = None, 
                 details: Any = None, payload: Dict = None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.code = code or f"ERROR_{status_code}"
        self.details = details
        self.payload = payload or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        rv = {
            'status': 'error',
            'code': self.code,
            'message': self.message,
            **self.payload
        }
        if self.details:
            rv['details'] = str(self.details)
        return rv

    def to_response(self) -> tuple:
        """Convert error to Flask response."""
        if request.is_json:
            return jsonify(self.to_dict()), self.status_code
        flash(self.message, 'error')
        return render_template('error.html', error=self), self.status_code

# Specific error types
class ValidationError(AppError):
    """Raised when input validation fails."""
    def __init__(self, message: str, details: Any = None):
        super().__init__(
            message=message,
            status_code=400,
            code="VALIDATION_ERROR",
            details=details
        )

class AuthenticationError(AppError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication required", details: Any = None):
        super().__init__(
            message=message,
            status_code=401,
            code="UNAUTHORIZED",
            details=details
        )

class AuthorizationError(AppError):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Insufficient permissions", details: Any = None):
        super().__init__(
            message=message,
            status_code=403,
            code="FORBIDDEN",
            details=details
        )

class NotFoundError(AppError):
    """Raised when a resource is not found."""
    def __init__(self, message: str = "Resource not found", details: Any = None):
        super().__init__(
            message=message,
            status_code=404,
            code="NOT_FOUND",
            details=details
        )

class DatabaseError(AppError):
    """Raised when a database operation fails."""
    def __init__(self, message: str = "Database operation failed", details: Any = None):
        super().__init__(
            message=message,
            status_code=500,
            code="DATABASE_ERROR",
            details=details
        )

class APIError(AppError):
    """Raised when an external API call fails."""
    def __init__(self, message: str = "API request failed", details: Any = None):
        super().__init__(
            message=message,
            status_code=502,
            code="API_ERROR",
            details=details
        )

class NetworkError(AppError):
    """Raised when a network operation fails."""
    def __init__(self, message: str = "Network operation failed", details: Any = None):
        super().__init__(
            message=message,
            status_code=503,
            code="NETWORK_ERROR",
            details=details
        )

class TimeoutError(AppError):
    """Raised when an operation times out."""
    def __init__(self, message: str = "Operation timed out", details: Any = None):
        super().__init__(
            message=message,
            status_code=504,
            code="TIMEOUT_ERROR",
            details=details
        )

class ConfigurationError(AppError):
    """Raised when there's a configuration error."""
    def __init__(self, message: str = "Configuration error", details: Any = None):
        super().__init__(
            message=message,
            status_code=500,
            code="CONFIGURATION_ERROR",
            details=details
        )

class RateLimitError(AppError):
    """Error raised when API rate limits are exceeded."""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            status_code=429,
            code="RATE_LIMIT_ERROR"
        )

def handle_error(error: Exception) -> tuple:
    """Global error handler for the application."""
    if isinstance(error, AppError):
        return error.to_response()
    
    if isinstance(error, HTTPException):
        return AppError(
            message=error.description,
            status_code=error.code,
            code=f"HTTP_{error.code}"
        ).to_response()
    
    # Log unexpected errors
    logger.error(f"Unexpected error: {str(error)}")
    logger.error(traceback.format_exc())
    
    return AppError(
        message="An unexpected error occurred",
        status_code=500,
        code="INTERNAL_ERROR",
        details=str(error)
    ).to_response()

def handle_errors(f: Callable) -> Callable:
    """Decorator to handle errors consistently."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return handle_error(e)
    return decorated_function

def validate_request_data(required_fields: list) -> Callable:
    """Decorator to validate request data."""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            data = request.get_json()
            if not data:
                raise ValidationError("No data provided")
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(
                    f"Missing required fields: {', '.join(missing_fields)}",
                    details={"missing_fields": missing_fields}
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def handle_api_error(f: Callable) -> Callable:
    """Decorator to handle API errors gracefully."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {f.__name__}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise APIError(details=str(e))
    return decorated_function 