from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class RefreshToken(BaseModel):
    """Модель refresh токенов"""
    
    __tablename__ = "refresh_tokens"
    
    user_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(512), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    
    # Связи
    user = relationship("User", back_populates="refresh_tokens")