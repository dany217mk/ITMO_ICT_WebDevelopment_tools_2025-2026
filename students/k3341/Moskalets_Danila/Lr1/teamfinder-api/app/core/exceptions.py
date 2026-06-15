"""Кастомные исключения для приложения"""
from typing import Any, Dict, Optional


class AppException(Exception):
    """Базовое исключение приложения"""
    def __init__(
        self, 
        status_code: int = 400, 
        message: str = "Bad request", 
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.message = message
        self.details = details
        super().__init__(self.message)


class UnauthorizedException(AppException):
    """Ошибка авторизации (401)"""
    def __init__(self, message: str = "Unauthorized", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, message=message, details=details)


class ForbiddenException(AppException):
    """Ошибка доступа (403)"""
    def __init__(self, message: str = "Forbidden", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=403, message=message, details=details)


class NotFoundException(AppException):
    """Ресурс не найден (404)"""
    def __init__(self, message: str = "Resource not found", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=404, message=message, details=details)


class ConflictException(AppException):
    """Конфликт данных (409)"""
    def __init__(self, message: str = "Conflict", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=409, message=message, details=details)


class ValidationException(AppException):
    """Ошибка валидации (422)"""
    def __init__(self, message: str = "Validation error", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=422, message=message, details=details)