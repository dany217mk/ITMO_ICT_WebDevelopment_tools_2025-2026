from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

# Используем TYPE_CHECKING для избежания циклических импортов
if TYPE_CHECKING:
    from app.schemas.skill import SkillResponse, ProficiencyLevel

# В runtime импортируем так
from app.schemas.skill import SkillResponse, ProficiencyLevel


class UserResponse(BaseModel):
    """Базовый ответ пользователя"""
    id: int
    role: str
    first_name: str
    last_name: str
    email: EmailStr
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserSkillResponse(BaseModel):
    """Навык пользователя с уровнем"""
    skill: SkillResponse
    proficiency_level: ProficiencyLevel
    
    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Детальный ответ пользователя (с навыками)"""
    skills: List[UserSkillResponse] = []


class UpdateProfileRequest(BaseModel):
    """Запрос на обновление профиля"""
    first_name: Optional[str] = Field(None, max_length=64)
    last_name: Optional[str] = Field(None, max_length=64)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """Запрос на смену пароля"""
    old_password: str
    new_password: str = Field(..., min_length=8)


class UserStatsResponse(BaseModel):
    """Статистика пользователя"""
    total_projects_owned: int = 0
    total_tasks_assigned: int = 0
    total_teams: int = 0
    total_completed_tasks: int = 0


class AddUserSkillRequest(BaseModel):
    """Запрос на добавление навыка пользователю"""
    skill_id: int
    proficiency_level: ProficiencyLevel