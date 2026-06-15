from datetime import date
from sqlalchemy import Column, String, Text, Date, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.models.base import BaseModel
from app.models.enums import ProjectStatus


class Project(BaseModel):
    """Модель проекта"""
    
    __tablename__ = "projects"
    
    owner_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(SQLAlchemyEnum(ProjectStatus), default=ProjectStatus.DRAFT, nullable=False)
    deadline = Column(Date, nullable=True)
    
    # Связи
    owner = relationship("User", back_populates="owned_projects", foreign_keys=[owner_id])
    teams = relationship("Team", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    required_skills = relationship("ProjectSkill", back_populates="project", cascade="all, delete-orphan")