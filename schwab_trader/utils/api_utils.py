"""Utility functions for API interactions."""
import logging
import time
from functools import wraps
from flask import current_app
from flask_caching import Cache

logger = logging.getLogger(__name__)

# Initialize cache
cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})

def retry_on_failure(max_retries=3, delay=1, backoff=2):
    """Decorator to retry API calls on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        wait_time = delay * (backoff ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                        raise last_exception
            return None
        return wrapper
    return decorator

def cache_response(timeout=300):
    """Decorator to cache API responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get cached response
            cached_response = cache.get(cache_key)
            if cached_response is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_response
            
            # If not in cache, call the function
            response = func(*args, **kwargs)
            
            # Cache the response
            cache.set(cache_key, response, timeout=timeout)
            logger.debug(f"Cached response for {cache_key}")
            
            return response
        return wrapper
    return decorator

def handle_api_error(func):
    """Decorator to handle API errors gracefully."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"API error in {func.__name__}: {str(e)}")
            if hasattr(e, 'response'):
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise
    return wrapper 