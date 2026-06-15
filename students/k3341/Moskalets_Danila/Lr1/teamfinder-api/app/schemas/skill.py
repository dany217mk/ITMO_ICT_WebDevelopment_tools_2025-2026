from pydantic import BaseModel, Field
from enum import Enum


class ProficiencyLevel(str, Enum):
    """Уровень владения навыком"""
    BEGINNER = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"


class SkillImportance(str, Enum):
    """Важность навыка для проекта"""
    NICE_TO_HAVE = "NICE_TO_HAVE"
    IMPORTANT = "IMPORTANT"
    REQUIRED = "REQUIRED"


class SkillResponse(BaseModel):
    """Ответ с навыком"""
    id: int
    name: str
    category: str
    
    class Config:
        from_attributes = True


class CreateSkillRequest(BaseModel):
    """Запрос на создание навыка"""
    name: str = Field(..., max_length=128, example="FastAPI")
    category: str = Field(..., max_length=64, example="Backend")