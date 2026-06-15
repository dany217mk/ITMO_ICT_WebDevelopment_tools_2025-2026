"""Модель ассоциации Team-User с ролью и статусом"""
from datetime import datetime
from sqlalchemy import Column, ForeignKey, DateTime, Enum as SQLAlchemyEnum, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.enums import TeamRole, MemberStatus


class TeamMember(Base):
    """Ассоциативная сущность Team-User с дополнительными полями
    
    Связывает пользователя с командой, добавляя:
    - role_in_team: роль пользователя в команде (LEAD, MEMBER, OBSERVER)
    - status: статус участия (INVITED, ACTIVE, LEFT, REMOVED)
    - joined_at: дата вступления
    """
    
    __tablename__ = "team_members"
    
    # Составной первичный ключ
    team_id = Column(ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True)
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    
    # Дополнительные поля связи
    role_in_team = Column(SQLAlchemyEnum(TeamRole), default=TeamRole.MEMBER, nullable=False)
    status = Column(SQLAlchemyEnum(MemberStatus), default=MemberStatus.ACTIVE, nullable=False)
    joined_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Связи (обратные ссылки)
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")