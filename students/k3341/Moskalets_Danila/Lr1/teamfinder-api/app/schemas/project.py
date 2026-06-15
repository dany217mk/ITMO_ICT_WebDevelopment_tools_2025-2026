from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from app.schemas.skill import SkillResponse, SkillImportance
    from app.schemas.team import TeamResponse

from app.schemas.skill import SkillResponse, SkillImportance


class ProjectStatus(str, Enum):
    """Статус проекта"""
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class ProjectResponse(BaseModel):
    """Базовый ответ проекта"""
    id: int
    owner_id: int
    title: str
    description: str
    status: ProjectStatus
    deadline: Optional[date] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProjectSkillResponse(BaseModel):
    """Навык проекта с важностью"""
    skill: SkillResponse
    importance: SkillImportance
    
    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Базовый ответ команды (для вложенности в Project)"""
    id: int
    project_id: int
    created_by: Optional[int]
    name: str
    description: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    """Детальный ответ проекта (с навыками и командами)"""
    required_skills: List[ProjectSkillResponse] = []
    teams: List["TeamResponse"] = []


class CreateProjectRequest(BaseModel):
    """Запрос на создание проекта"""
    title: str = Field(..., max_length=256, example="AI Chatbot")
    description: str = Field(..., example="Developing an AI-powered chatbot")
    deadline: Optional[date] = None


class UpdateProjectRequest(BaseModel):
    """Запрос на обновление проекта"""
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    deadline: Optional[date] = None


class AddProjectSkillRequest(BaseModel):
    """Запрос на добавление навыка проекту"""
    skill_id: int
    importance: SkillImportance


# Forward reference fix
ProjectDetailResponse.model_rebuild()