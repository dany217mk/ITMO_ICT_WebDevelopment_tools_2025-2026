from datetime import date
from sqlalchemy import Column, String, Text, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import TaskStatus, TaskPriority


class Task(BaseModel):
    """Модель задачи"""
    
    __tablename__ = "tasks"
    
    project_id = Column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    assignee_id = Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLAlchemyEnum(TaskStatus), default=TaskStatus.TODO, nullable=False)
    priority = Column(SQLAlchemyEnum(TaskPriority), default=TaskPriority.MEDIUM, nullable=False)
    due_date = Column(Date, nullable=True)
    
    # Связи
    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks", foreign_keys=[assignee_id])