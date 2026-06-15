from sqlalchemy import Column, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import ProficiencyLevel


class UserSkill(Base):
    """Ассоциация User-Skill с уровнем владения"""
    
    __tablename__ = "user_skills"
    
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    proficiency_level = Column(SQLAlchemyEnum(ProficiencyLevel), nullable=False)
    
    # Связи
    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")