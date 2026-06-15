from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class ErrorDetail(BaseModel):
    """Детали ошибки"""
    code: int = Field(..., example=404)
    message: str = Field(..., example="Resource not found")
    details: Optional[Dict[str, Any]] = Field(None, description="Дополнительные сведения об ошибке")


class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой"""
    error: ErrorDetail


class ValidationErrorItem(BaseModel):
    """Элемент валидационной ошибки"""
    loc: List[str] = Field(..., example=["body", "email"])
    msg: str = Field(..., example="field required")
    type: str = Field(..., example="missing")


class ValidationErrorResponse(BaseModel):
    """Ответ с ошибкой валидации"""
    error: ErrorDetail = Field(
        default=ErrorDetail(code=422, message="Validation error", details=None)
    )