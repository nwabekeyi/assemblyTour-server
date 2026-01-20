from pydantic import BaseModel, Field
from typing import Optional, Literal
from typing_extensions import Annotated

class AuthData(BaseModel):
    action: Literal['register', 'login', 'refresh']

    # Fields
    username: Optional[Annotated[str, Field(min_length=3, max_length=30)]]
    phone: Optional[Annotated[str, Field(min_length=10, max_length=15)]]
    password: Optional[Annotated[str, Field(min_length=6)]]
    refresh: Optional[str]
    turnstileToken: Optional[str]  # ✅ added token field

    @classmethod
    def model_validate(cls, values: dict) -> dict:
        action = values.get('action')

        if action == 'register':
            required_fields = ['phone', 'turnstileToken']  # ✅ require token for registration
        elif action == 'login':
            required_fields = ['username', 'password']
        elif action == 'refresh':
            required_fields = ['refresh']
        else:
            return values

        missing = [f for f in required_fields if not values.get(f)]
        if missing:
            raise ValueError(f"Missing required fields for {action}: {', '.join(missing)}")

        return values