
from rest_framework.views import exception_handler
from .api_response import api_response

def custom_exception_handler(exc, context):
    """
    Wrap all exceptions into a consistent API response
    """
    # Call default DRF handler first
    response = exception_handler(exc, context)

    if response is not None:
        # Extract errors from DRF
        errors = response.data
        message = "An error occurred"

        # Customize message for common cases
        if isinstance(errors, dict):
            message = next(iter(errors))  # first key as message

        return api_response(
            success=False,
            message=message,
            data=None,
            errors=errors,
            status_code=response.status_code
        )

    # If DRF couldn't handle it, fallback to generic 500
    return api_response(
        success=False,
        message="Internal server error",
        data=None,
        errors=str(exc),
        status_code=500
    )