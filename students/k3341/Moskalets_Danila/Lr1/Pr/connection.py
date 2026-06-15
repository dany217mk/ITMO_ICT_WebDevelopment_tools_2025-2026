from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import NullPool

# URL подключения к БД
# postgresql://пользователь:пароль@хост:порт/имя_базы
db_url = 'postgresql://postgres:password@localhost:5432/warriors_db'

# Создаем движок БД
# echo=True - выводит все SQL-запросы в консоль (полезно для отладки)
engine = create_engine(db_url, echo=True, poolclass=NullPool)

def init_db():
    """Создает все таблицы в БД на основе моделей"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Генератор сессий для Dependency Injection"""
    with Session(engine) as session:
        yield session