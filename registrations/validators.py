from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict
from typing_extensions import Annotated
from datetime import date

STEP_CHOICES = ['details', 'payment', 'documents', 'visa', 'hotel', 'flight', 'completed']

class HajjStepData(BaseModel):
    step: Literal['details', 'payment', 'documents', 'visa', 'hotel', 'flight', 'completed']

    # Optional data for each step
    personal_info: Optional[Dict] = None
    payment_info: Optional[Dict] = None
    documents_info: Optional[Dict] = None
    visa_info: Optional[Dict] = None
    hotel_info: Optional[Dict] = None
    flight_info: Optional[Dict] = None

    # ✅ Pydantic v2 style root validator
    @classmethod
    def model_validate(cls, values: dict) -> dict:
        step = values.get('step')

        if step not in STEP_CHOICES:
            raise ValueError(f"Invalid step: {step}")

        # Define required payload per step
        required_fields_map = {
            'details': ['personal_info'],
            'payment': ['payment_info'],
            'documents': ['documents_info'],
            'visa': ['visa_info'],
            'hotel': ['hotel_info'],
            'flight': ['flight_info'],
            'completed': []
        }

        missing = [
            field for field in required_fields_map.get(step, [])
            if not values.get(field)
        ]

        if missing:
            raise ValueError(f"Missing required fields for step '{step}': {', '.join(missing)}")

        return values
