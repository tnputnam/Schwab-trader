from django.contrib import messages

def feedback_messages(request):
    """Context processor to provide consistent feedback messages."""
    return {
        'feedback_messages': {
            'success': {
                'strategy_created': 'Strategy created successfully.',
                'strategy_updated': 'Strategy updated successfully.',
                'strategy_deleted': 'Strategy deleted successfully.',
                'backtest_started': 'Backtest started successfully.',
                'backtest_completed': 'Backtest completed successfully.',
                'portfolio_imported': 'Portfolio imported successfully.',
                'position_added': 'Position added successfully.',
                'position_updated': 'Position updated successfully.',
                'position_deleted': 'Position deleted successfully.',
            },
            'error': {
                'strategy_not_found': 'Strategy not found.',
                'backtest_failed': 'Backtest failed. Please check the logs for details.',
                'portfolio_import_failed': 'Failed to import portfolio. Please check the file format.',
                'position_not_found': 'Position not found.',
                'invalid_input': 'Invalid input. Please check your data.',
                'database_error': 'Database error occurred. Please try again.',
                'permission_denied': 'You do not have permission to perform this action.',
            },
            'warning': {
                'strategy_inactive': 'Strategy is currently inactive.',
                'backtest_in_progress': 'Backtest is already in progress.',
                'portfolio_empty': 'Portfolio is empty.',
                'position_closed': 'Position is already closed.',
            },
            'info': {
                'strategy_activation': 'Strategy will be activated on the next market open.',
                'backtest_queued': 'Backtest has been queued for processing.',
                'portfolio_syncing': 'Portfolio is being synced with broker.',
                'position_pending': 'Position is pending execution.',
            }
        }
    }

def error_responses(request):
    """Context processor to provide error responses to templates."""
    return {
        'error_response': getattr(request, 'error_responses', [])[-1] if hasattr(request, 'error_responses') and request.error_responses else None
    } 