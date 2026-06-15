from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Skill(BaseModel):
    """Справочник навыков"""
    
    __tablename__ = "skills"
    
    name = Column(String(128), unique=True, index=True, nullable=False)
    category = Column(String(64), nullable=False)
    
    # Связи
    user_skills = relationship("UserSkill", back_populates="skill", cascade="all, delete-orphan")
    project_skills = relationship("ProjectSkill", back_populates="skill", cascade="all, delete-orphan")