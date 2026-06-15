from datetime import datetime
from sqlalchemy import Column, BigInteger, DateTime, func
from sqlalchemy.ext.declarative import declared_attr

from app.core.database import Base


class BaseModel(Base):
    """Абстрактная базовая модель с общими полями"""
    
    __abstract__ = True
    
    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    