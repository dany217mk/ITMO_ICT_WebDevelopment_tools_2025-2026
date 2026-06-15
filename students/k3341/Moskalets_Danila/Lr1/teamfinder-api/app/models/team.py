from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Team(BaseModel):
    """Модель команды"""
    
    __tablename__ = "teams"
    
    project_id = Column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    
    # Связи
    project = relationship("Project", back_populates="teams")
    creator = relationship("User", back_populates="created_teams", foreign_keys=[created_by])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")