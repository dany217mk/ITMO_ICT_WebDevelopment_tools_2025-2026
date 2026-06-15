from app.tasks.celery_app import celery_app
from app.tasks.parser_tasks import parse_url_task, parse_all_task

__all__ = ["celery_app", "parse_url_task", "parse_all_task"]