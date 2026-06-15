from datetime import datetime
from sqlalchemy import Column, String, Boolean, Text, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import UserRole


class User(BaseModel):
    """Модель пользователя"""
    
    __tablename__ = "users"
    
    # Основные поля
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Связи
    # Будет заполнено после создания связанных моделей
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    created_teams = relationship("Team", back_populates="creator", foreign_keys="Team.created_by")
    assigned_tasks = relationship("Task", back_populates="assignee", foreign_keys="Task.assignee_id")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    
    # Many-to-Many связи (через ассоциативные таблицы)
    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    team_memberships = relationship("TeamMember", back_populates="user", cascade="all, delete-orphan")