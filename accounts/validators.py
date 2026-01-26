from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from typing_extensions import Annotated
import re

class AuthData(BaseModel):
    action: Literal['register', 'login', 'refresh']

    username: Optional[Annotated[str, Field(min_length=3, max_length=30)]]
    phone: Optional[str]
    password: Optional[Annotated[str, Field(min_length=6)]]
    refresh: Optional[str]
    turnstileToken: Optional[str]

    # ✅ Phone validation
    @field_validator("phone")
    @classmethod
    def validate_nigerian_phone(cls, v):
        if v is None:
            return v

        if not v.startswith("+234"):
            raise ValueError("Phone number must start with +234")

        digits_only = v[1:]  # remove +

        if not digits_only.isdigit():
            raise ValueError("Phone number must contain only digits after +")

        if len(digits_only) != 13:
            raise ValueError("Phone number must be exactly 13 digits excluding '+'")

        return v

    # ✅ Action-based validation
    @classmethod
    def model_validate(cls, values: dict):
        action = values.get('action')

        if action == 'register':
            required_fields = ['phone', 'turnstileToken']
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
