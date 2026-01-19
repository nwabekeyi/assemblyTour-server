from pydantic import BaseModel, Field
from typing import Optional, Literal
from typing_extensions import Annotated

EMAIL_REGEX = r'^[^@]+@[^@]+\.[^@]+$'

class AuthData(BaseModel):
    action: Literal['register', 'login', 'refresh']

    # Registration fields
    username: Optional[Annotated[str, Field(min_length=3, max_length=30)]]
    email: Optional[Annotated[str, Field(pattern=EMAIL_REGEX)]]
    phone: Optional[Annotated[str, Field(min_length=10, max_length=15)]]

    # Login fields
    password: Optional[Annotated[str, Field(min_length=6)]]
    refresh: Optional[str]  # for refresh token

    # ✅ Pydantic v2 replacement for root_validator
    @classmethod
    def model_validate(cls, values: dict) -> dict:
        # Retrieve action from incoming payload
        action = values.get('action')

        if action == 'register':
            required_fields = ['username', 'email', 'phone']
        elif action == 'login':
            required_fields = ['email', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            # If action is not provided or unknown, skip validation
            return values

        # Check for missing required fields
        missing = [field for field in required_fields if not values.get(field)]
        if missing:
            raise ValueError(f"Missing required fields for {action}: {', '.join(missing)}")

        return values
