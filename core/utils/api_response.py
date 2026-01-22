# core/utils/api_response.py
from rest_framework.response import Response

def api_response(data=None, message="", success=True, errors=None, status_code=200):
    """
    Standard API response format.
    All apps should use this function to return responses.
    """
    return Response(
        {
            "success": success,
            "message": message,
            "data": data,
            "errors": errors
        },
        status=status_code
    )