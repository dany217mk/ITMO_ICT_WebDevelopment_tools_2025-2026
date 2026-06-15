# connection.py
import os
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Получаем URL базы данных из переменных окружения
db_url = os.getenv('DB_ADMIN', 'postgresql://postgres:123@localhost:5432/warriors_db')

# Дополнительные параметры для подключения
# echo=True - выводит SQL-запросы в консоль (только для разработки)
echo_mode = os.getenv('DEBUG', 'True').lower() == 'true'

# Создаем движок БД
engine = create_engine(
    db_url,
    echo=echo_mode,
    poolclass=NullPool,
    pool_pre_ping=True  # Проверяет соединение перед использованием
)

def init_db():
    """Создает все таблицы в БД на основе моделей"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Генератор сессий для Dependency Injection"""
    with Session(engine) as session:
        yield session