from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from typing_extensions import Annotated
import re

class AuthData(BaseModel):
    action: Literal['register', 'login', 'refresh']

    username: Optional[Annotated[str, Field(min_length=3, max_length=30)]]
    email: Optional[Annotated[str, Field(max_length=254)]]
    password: Optional[Annotated[str, Field(min_length=6)]]
    refresh: Optional[str]
    turnstileToken: Optional[str]
    package_id: Optional[int]

    # ✅ Email validation
    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        if v is None:
            return v

        if v and '@' not in v:
            raise ValueError("Invalid email address")

        return v

    # ✅ Action-based validation
    @classmethod
    def model_validate(cls, values: dict):
        action = values.get('action')

        if action == 'register':
            required_fields = ['email']
        elif action == 'login':
            required_fields = ['username', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            return values

        missing = [f for f in required_fields if not values.get(f)]
        if missing:
            raise ValueError(
                f"Missing required fields for {action}: {', '.join(missing)}"
            )

        return values
