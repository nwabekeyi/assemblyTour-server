# core/utils/validators.py
from pydantic import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

def validate_with_pydantic(schema_class, data):
    """
    Validates input data against a Pydantic schema.
    Converts Pydantic ValidationError into DRF ValidationError
    so it integrates well with Django REST Framework.
    """
    try:
        validated_data = schema_class.model_validate(data)  # Pydantic v2
        return validated_data
    except ValidationError as e:
        # Convert Pydantic errors to DRF ValidationError format
        errors = {err['loc'][0]: err['msg'] for err in e.errors()}
        raise DRFValidationError(errors)
    except ValueError as e:
        # For manual ValueError from model_validate
        raise DRFValidationError(str(e))
