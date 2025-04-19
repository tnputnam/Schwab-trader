# Error Handling in Schwab Trader

This document outlines the error handling system used throughout the Schwab Trader application.

## Overview

The error handling system provides a consistent way to handle and report errors across the application. It includes:

- Standardized error responses
- Proper error logging
- Content negotiation (JSON/HTML)
- Error decorators for common use cases

## Error Response Format

All error responses follow this structure:

```json
{
    "status": "error",
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Optional detailed error information"
}
```

## Error Types

### AppError

The base error class for all application errors. Usage:

```python
raise AppError(
    message="Error message",
    status_code=400,
    code="ERROR_CODE",
    details="Additional details"
)
```

### Common Error Codes

- `INVALID_INPUT`: Invalid user input (400)
- `NOT_FOUND`: Resource not found (404)
- `UNAUTHORIZED`: Authentication required (401)
- `FORBIDDEN`: Insufficient permissions (403)
- `INTERNAL_ERROR`: Server error (500)
- `API_ERROR`: External API error (502)
- `DATABASE_ERROR`: Database operation failed (500)
- `VALIDATION_ERROR`: Data validation failed (400)

## Error Decorators

### @handle_errors

Basic error handling decorator for routes:

```python
@bp.route('/endpoint')
@handle_errors
def endpoint():
    # Your code here
```

### @handle_api_error

Specialized decorator for API calls:

```python
@bp.route('/api/endpoint')
@handle_api_error
@handle_errors
def api_endpoint():
    # Your code here
```

### @validate_request_data

Decorator for request data validation:

```python
@bp.route('/api/data')
@validate_request_data(['required_field1', 'required_field2'])
@handle_errors
def data_endpoint():
    # Your code here
```

## Best Practices

1. **Use Specific Error Codes**
   - Always provide a specific error code
   - Use existing codes when possible
   - Create new codes for new error types

2. **Provide Helpful Messages**
   - Make error messages user-friendly
   - Include actionable information
   - Avoid exposing sensitive details

3. **Log Errors Properly**
   - Use the appropriate log level
   - Include relevant context
   - Log stack traces for unexpected errors

4. **Handle Errors at the Right Level**
   - Use decorators for route-level errors
   - Handle specific exceptions when possible
   - Let unexpected errors propagate to the global handler

## Example Usage

### Basic Route

```python
@bp.route('/data')
@handle_errors
def get_data():
    try:
        data = get_data_from_db()
        return jsonify({'status': 'success', 'data': data})
    except DatabaseError as e:
        raise AppError(
            message="Failed to fetch data",
            status_code=500,
            code="DATABASE_ERROR",
            details=str(e)
        )
```

### API Endpoint

```python
@bp.route('/api/external')
@handle_api_error
@handle_errors
def external_api():
    response = make_api_call()
    return jsonify({'status': 'success', 'data': response})
```

### Data Validation

```python
@bp.route('/api/submit')
@validate_request_data(['name', 'email'])
@handle_errors
def submit_data():
    data = request.get_json()
    # Process validated data
```

## Error Response Examples

### JSON Response

```json
{
    "status": "error",
    "code": "INVALID_INPUT",
    "message": "Email address is required",
    "details": {
        "field": "email",
        "reason": "missing"
    }
}
```

### HTML Response

For non-API requests, errors are rendered as HTML pages with flash messages.

## Testing Error Handling

When testing error handling:

1. Test both success and error cases
2. Verify error messages and codes
3. Check response formats
4. Ensure proper logging
5. Test error propagation

## Troubleshooting

Common issues and solutions:

1. **Error not being caught**
   - Ensure proper decorator order
   - Check error inheritance
   - Verify error handler registration

2. **Incorrect response format**
   - Check content negotiation
   - Verify error structure
   - Test with different request types

3. **Missing error details**
   - Add appropriate error context
   - Include relevant stack traces
   - Provide actionable information 