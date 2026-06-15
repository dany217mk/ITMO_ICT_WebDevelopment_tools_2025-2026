from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class TaskStatus(str, Enum):
    """Статус задачи"""
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    DONE = "DONE"


class TaskPriority(str, Enum):
    """Приоритет задачи"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TaskResponse(BaseModel):
    """Ответ с задачей"""
    id: int
    project_id: int
    assignee_id: Optional[int]
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CreateTaskRequest(BaseModel):
    """Запрос на создание задачи"""
    title: str = Field(..., max_length=256, example="Setup database")
    description: Optional[str] = Field(None, example="Create PostgreSQL schema")
    assignee_id: Optional[int] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[date] = None


class UpdateTaskRequest(BaseModel):
    """Запрос на обновление задачи"""
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[date] = None