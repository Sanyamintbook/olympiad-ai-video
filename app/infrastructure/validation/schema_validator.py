from typing import Any
from pydantic import BaseModel, ValidationError

class ValidationResult(BaseModel):
    is_valid: bool
    errors: list[str]

class SchemaValidator:
    """
    Enforces structural correctness at every stage boundary.
    Can validate dicts, lists of dicts, or Pydantic model instances.
    """
    def validate(self, artifact: Any, model_type: type[BaseModel]) -> ValidationResult:
        errors = []
        try:
            if isinstance(artifact, list):
                for index, item in enumerate(artifact):
                    try:
                        if isinstance(item, dict):
                            model_type.model_validate(item)
                        elif isinstance(item, BaseModel):
                            model_type.model_validate(item.model_dump())
                        else:
                            model_type.model_validate(item)
                    except ValidationError as e:
                        for err in e.errors():
                            loc = " -> ".join(str(l) for l in err["loc"])
                            errors.append(f"Item {index} [{loc}]: {err['msg']}")
            else:
                try:
                    if isinstance(artifact, dict):
                        model_type.model_validate(artifact)
                    elif isinstance(artifact, BaseModel):
                        model_type.model_validate(artifact.model_dump())
                    else:
                        model_type.model_validate(artifact)
                except ValidationError as e:
                    for err in e.errors():
                        loc = " -> ".join(str(l) for l in err["loc"])
                        errors.append(f"[{loc}]: {err['msg']}")
        except Exception as e:
            errors.append(f"Unexpected error during validation: {str(e)}")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
