from django.contrib import messages

def send_feedback(request, message_type, message_key, **kwargs):
    """
    Send a feedback message to the user.
    
    Args:
        request: The request object
        message_type: The type of message ('success', 'error', 'warning', 'info')
        message_key: The key of the message in the feedback_messages dictionary
        **kwargs: Additional parameters to format the message
    """
    try:
        message = request.feedback_messages[message_type][message_key]
        if kwargs:
            message = message.format(**kwargs)
        getattr(messages, message_type)(request, message)
    except (KeyError, AttributeError):
        # Fallback to a generic message if the specific message is not found
        generic_messages = {
            'success': 'Operation completed successfully.',
            'error': 'An error occurred.',
            'warning': 'Please note: {message_key}',
            'info': 'Information: {message_key}'
        }
        getattr(messages, message_type)(request, generic_messages[message_type].format(message_key=message_key))

class ErrorResponse:
    """Class to handle and format error responses for user actions."""
    
    ERROR_TYPES = {
        'button_disabled': {
            'type': 'warning',
            'title': 'Action Not Available',
            'message': 'This action is currently disabled.',
            'details': None
        },
        'invalid_input': {
            'type': 'danger',
            'title': 'Invalid Input',
            'message': 'Please check your input and try again.',
            'details': None
        },
        'network_error': {
            'type': 'danger',
            'title': 'Connection Error',
            'message': 'Unable to connect to the server. Please check your connection.',
            'details': None
        },
        'permission_denied': {
            'type': 'danger',
            'title': 'Permission Denied',
            'message': 'You do not have permission to perform this action.',
            'details': None
        },
        'operation_failed': {
            'type': 'danger',
            'title': 'Operation Failed',
            'message': 'The operation could not be completed.',
            'details': None
        },
        'validation_error': {
            'type': 'danger',
            'title': 'Validation Error',
            'message': 'The provided data is invalid.',
            'details': None
        },
        'timeout': {
            'type': 'warning',
            'title': 'Operation Timed Out',
            'message': 'The operation took too long to complete.',
            'details': None
        },
        'maintenance': {
            'type': 'info',
            'title': 'System Maintenance',
            'message': 'This feature is currently under maintenance.',
            'details': None
        }
    }

    def __init__(self, error_type, details=None, custom_message=None):
        """
        Initialize an error response.
        
        Args:
            error_type: The type of error from ERROR_TYPES
            details: Additional error details (optional)
            custom_message: Custom message to override the default (optional)
        """
        if error_type not in self.ERROR_TYPES:
            raise ValueError(f"Invalid error type: {error_type}")
        
        self.error_type = error_type
        self.details = details
        self.custom_message = custom_message

    def to_dict(self):
        """Convert the error response to a dictionary for template rendering."""
        error_info = self.ERROR_TYPES[self.error_type].copy()
        if self.custom_message:
            error_info['message'] = self.custom_message
        if self.details:
            error_info['details'] = str(self.details)
        return error_info

    @classmethod
    def create_response(cls, error_type, details=None, custom_message=None):
        """Create and return an error response dictionary."""
        return cls(error_type, details, custom_message).to_dict()

def handle_action_error(request, error_type, details=None, custom_message=None):
    """
    Handle an action error and add it to the request context.
    
    Args:
        request: The request object
        error_type: The type of error from ErrorResponse.ERROR_TYPES
        details: Additional error details (optional)
        custom_message: Custom message to override the default (optional)
    """
    error_response = ErrorResponse.create_response(error_type, details, custom_message)
    if not hasattr(request, 'error_responses'):
        request.error_responses = []
    request.error_responses.append(error_response)
    return error_response 