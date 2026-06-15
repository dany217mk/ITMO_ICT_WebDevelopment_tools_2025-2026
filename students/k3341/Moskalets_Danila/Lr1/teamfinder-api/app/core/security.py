"""Модуль для работы с безопасностью: хэширование паролей и JWT токены"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    # Настройки Argon2 (можно оставить по умолчанию)
    argon2__time_cost=2,      # Количество итераций
    argon2__memory_cost=102400,  # Память в KB (100 MB)
    argon2__parallelism=8,     # Количество потоков
    argon2__hash_len=32,       # Длина хэша
    argon2__salt_len=16,       # Длина соли
)


def hash_password(password: str) -> str:
    """
    Хэширование пароля с помощью Argon2
    
    Args:
        password: Пароль в открытом виде (нет ограничения на длину)
        
    Returns:
        Хэшированный пароль
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля
    
    Args:
        plain_password: Пароль в открытом виде
        hashed_password: Хэшированный пароль из БД
        
    Returns:
        True если пароль совпадает
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Создание JWT access токена
    
    Args:
        data: Данные для кодирования в токен (обычно {'sub': user_id})
        expires_delta: Время жизни токена (по умолчанию из настроек)
        
    Returns:
        JWT токен в виде строки
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Создание JWT refresh токена
    
    Args:
        data: Данные для кодирования в токен (обычно {'sub': user_id})
        
    Returns:
        Refresh токен в виде строки
    """
    to_encode = data.copy()
    
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Декодирование JWT токена
    
    Args:
        token: JWT токен
        
    Returns:
        Декодированные данные или None при ошибке
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def get_token_user_id(token: str) -> Optional[int]:
    """
    Извлечение user_id из токена
    
    Args:
        token: JWT токен
        
    Returns:
        user_id или None
    """
    payload = decode_token(token)
    if payload:
        user_id = payload.get("sub")
        if user_id:
            return int(user_id)
    return None