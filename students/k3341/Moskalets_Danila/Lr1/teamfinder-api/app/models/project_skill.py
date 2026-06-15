from sqlalchemy import Column, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import SkillImportance


class ProjectSkill(Base):
    """Ассоциация Project-Skill с важностью"""
    
    __tablename__ = "project_skills"
    
    project_id = Column(ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    importance = Column(SQLAlchemyEnum(SkillImportance), nullable=False)
    
    # Связи
    project = relationship("Project", back_populates="required_skills")
    skill = relationship("Skill", back_populates="project_skills")