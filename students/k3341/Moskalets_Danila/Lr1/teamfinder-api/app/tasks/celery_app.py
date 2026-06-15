"""
Настройка Celery для асинхронных задач
"""
from celery import Celery
from app.core.config import settings

# Настройки Redis
REDIS_URL = settings.REDIS_URL if hasattr(settings, 'REDIS_URL') else "redis://redis:6379/0"

# Создаем Celery приложение
celery_app = Celery(
    "teamfinder",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks.parser_tasks"]
)

# Конфигурация Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 минут
    task_soft_time_limit=25 * 60,
    result_expires=3600,  # Результаты хранятся 1 час
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Настройка периодических задач (опционально)
celery_app.conf.beat_schedule = {
    'parse-all-every-hour': {
        'task': 'app.tasks.parser_tasks.parse_all_task',
        'schedule': 3600.0,  # каждый час
        'options': {'queue': 'parser'}
    },
}