from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Запрос на регистрацию"""
    first_name: str = Field(..., max_length=64, example="John")
    last_name: str = Field(..., max_length=64, example="Doe")
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., min_length=6, example="securepassword123")


class LoginRequest(BaseModel):
    """Запрос на вход"""
    email: EmailStr = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="securepassword123")


class TokenResponse(BaseModel):
    """Ответ с токенами"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена"""
    refresh_token: str