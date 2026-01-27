from pydantic import BaseModel, Field, ValidationError
from typing import Optional, Annotated


# --------------------------
# CREATE COMMENT VALIDATION
# --------------------------
class BlogCommentCreateData(BaseModel):
    content: Annotated[str, Field(min_length=2, max_length=2000)]
    parent_id: Optional[int] = Field(None, ge=1)

    @classmethod
    def validate_content(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Comment cannot be empty")
        return cleaned


# --------------------------
# LIKE/UNLIKE VALIDATION
# --------------------------
class BlogLikeToggleData(BaseModel):
    pass


# --------------------------
# HELPER FUNCTION
# --------------------------
def validate_or_raise(data: dict, model_class):
    try:
        return model_class.model_validate(data)
    except ValidationError as exc:
        errors = {}
        for e in exc.errors():
            loc = ".".join(str(x) for x in e["loc"]) if e["loc"] else "non_field_errors"
            errors.setdefault(loc, []).append(e["msg"])
        from rest_framework.exceptions import ValidationError as DRFValidationError
        raise DRFValidationError(detail=errors) from exc
