"""Роутер для аутентификации и авторизации"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedException, ConflictException
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация нового пользователя"
)
async def register(
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    - **first_name**: Имя (макс 64 символа)
    - **last_name**: Фамилия (макс 64 символа)
    - **email**: Адрес электронной почты
    - **password**: Пароль (минимум 6 символов)
    """
    auth_service = AuthService(db)
    
    try:
        user = await auth_service.register(data)
        return user
    except ConflictException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход в систему (получение JWT)"
)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Аутентификация пользователя и получение токенов
    
    - **email**: Адрес электронной почты
    - **password**: Пароль
    
    Возвращает access_token и refresh_token
    """
    auth_service = AuthService(db)
    
    try:
        user, access_token, refresh_token = await auth_service.login(data.email, data.password)
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer"
        )
    except UnauthorizedException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Обновить access-токен"
)
async def refresh_tokens(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление пары токенов по refresh_token
    
    - **refresh_token**: Refresh токен из предыдущего ответа
    """
    auth_service = AuthService(db)
    
    try:
        new_access_token, new_refresh_token = await auth_service.refresh_tokens(data.refresh_token)
        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer"
        )
    except UnauthorizedException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Выход из системы"
)
async def logout(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Выход из системы - ревокация refresh токена
    """
    auth_service = AuthService(db)
    await auth_service.logout(refresh_token)
    return None


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Получить текущего пользователя"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Получение информации о текущем аутентифицированном пользователе
    """
    return current_user