"""Dependencies для FastAPI (зависимости, используемые в роутерах)"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.core.exceptions import UnauthorizedException, NotFoundException
from app.models.user import User
from app.models.enums import UserRole

# Настройка bearer token аутентификации
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Получение текущего аутентифицированного пользователя
    
    Args:
        credentials: Bearer токен из заголовка Authorization
        db: Сессия БД
        
    Returns:
        Объект User
        
    Raises:
        UnauthorizedException: Если токен отсутствует, невалидный или пользователь не найден
    """
    if not credentials:
        raise UnauthorizedException(message="Not authenticated")
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(message="Invalid or expired token")
    
    # Проверяем тип токена (должен быть access)
    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid token type")
    
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(message="Invalid token payload")
    
    # Получаем пользователя из БД
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise NotFoundException(message="User not found")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Получение текущего активного пользователя (проверка is_verified)
    """
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Получение текущего администратора
    
    Raises:
        ForbiddenException: Если пользователь не администратор
    """
    if current_user.role != UserRole.ADMIN:
        from app.core.exceptions import ForbiddenException
        raise ForbiddenException(message="Admin access required")
    return current_user


def get_user_if_authenticated(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> Optional[int]:
    """
    Получение user_id если пользователь аутентифицирован (опционально)
    Используется для эндпоинтов, где авторизация не обязательна
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        return None
    
    user_id = payload.get("sub")
    return int(user_id) if user_id else None