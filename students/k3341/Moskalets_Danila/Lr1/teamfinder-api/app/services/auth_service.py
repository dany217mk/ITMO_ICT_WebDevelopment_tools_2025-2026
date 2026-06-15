"""Сервис для аутентификации и авторизации"""
from datetime import datetime, timedelta
from typing import Tuple, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.models.enums import UserRole
from app.core.security import (
    hash_password, 
    verify_password, 
    create_access_token, 
    create_refresh_token,
    decode_token
)
from app.core.exceptions import UnauthorizedException, ConflictException, NotFoundException
from app.schemas.auth import RegisterRequest, TokenResponse


class AuthService:
    """Сервис для работы с аутентификацией"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def register(self, data: RegisterRequest) -> User:
        """
        Регистрация нового пользователя
        
        Args:
            data: Данные для регистрации
            
        Returns:
            Созданный пользователь
            
        Raises:
            ConflictException: Если email уже используется
        """
        # Проверяем существует ли пользователь с таким email
        existing = await self.db.execute(
            select(User).where(User.email == data.email)
        )
        if existing.scalar_one_or_none():
            raise ConflictException(message="User with this email already exists")
        
        # Создаем пользователя
        user = User(
            first_name=data.first_name,
            last_name=data.last_name,
            email=data.email,
            password_hash=hash_password(data.password),
            role=UserRole.USER,
            is_verified=True,  # TODO: email verification
        )
        
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        await self.db.commit() 
        
        return user
    
    async def login(self, email: str, password: str) -> Tuple[User, str, str]:
        """
        Аутентификация пользователя
        
        Args:
            email: Email пользователя
            password: Пароль
            
        Returns:
            Кортеж (user, access_token, refresh_token)
            
        Raises:
            UnauthorizedException: Если email или пароль неверны
        """
        # Ищем пользователя
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException(message="Invalid email or password")
        
        # Создаем токены
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Сохраняем refresh token в БД
        refresh_token_obj = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False
        )
        self.db.add(refresh_token_obj)
        await self.db.commit()
        
        return user, access_token, refresh_token
    
    async def refresh_tokens(self, refresh_token: str) -> Tuple[str, str]:
        """
        Обновление токенов по refresh токену
        
        Args:
            refresh_token: Refresh токен
            
        Returns:
            Кортеж (new_access_token, new_refresh_token)
            
        Raises:
            UnauthorizedException: Если токен невалидный или ревокнут
        """
        # Проверяем токен в БД
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token == refresh_token,
                RefreshToken.revoked == False
            )
        )
        stored_token = result.scalar_one_or_none()
        
        if not stored_token:
            raise UnauthorizedException(message="Invalid refresh token")
        
        # Проверяем не истек ли токен
        if stored_token.expires_at < datetime.utcnow():
            raise UnauthorizedException(message="Refresh token expired")
        
        # Декодируем токен
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid refresh token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedException(message="Invalid token payload")
        
        # Ревокация старого токена
        stored_token.revoked = True
        
        # Создаем новые токены
        new_access_token = create_access_token(data={"sub": str(user_id)})
        new_refresh_token = create_refresh_token(data={"sub": str(user_id)})
        
        # Сохраняем новый refresh токен
        new_refresh_token_obj = RefreshToken(
            user_id=int(user_id),
            token=new_refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=7),
            revoked=False
        )
        self.db.add(new_refresh_token_obj)
        await self.db.commit()
        
        return new_access_token, new_refresh_token
    
    async def logout(self, refresh_token: str) -> None:
        """
        Выход из системы (ревокация refresh токена)
        
        Args:
            refresh_token: Refresh токен для ревокации
        """
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == refresh_token)
        )
        token = result.scalar_one_or_none()
        
        if token:
            token.revoked = True
            await self.db.commit()
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()