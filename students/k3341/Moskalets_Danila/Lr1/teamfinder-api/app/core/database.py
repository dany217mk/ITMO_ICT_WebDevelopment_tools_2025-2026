from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings 

# Создаем асинхронный движок
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Базовый класс для моделей
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Depends - получение сессии БД"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()