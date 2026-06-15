"""
Celery задачи для парсинга
"""
from celery import shared_task
from app.parser_service import run_parser_sync


@shared_task(name="parse_url_task", bind=True, queue="parser")
def parse_url_task(self, url: str):
    """
    Задача на парсинг конкретного URL
    """
    try:
        result = run_parser_sync(url=url)
        return {
            "task_id": self.request.id,
            "status": "completed",
            "url": url,
            "result": result
        }
    except Exception as e:
        return {
            "task_id": self.request.id,
            "status": "failed",
            "url": url,
            "error": str(e)
        }


@shared_task(name="parse_all_task", bind=True, queue="parser")
def parse_all_task(self):
    """
    Задача на парсинг всех источников
    """
    try:
        result = run_parser_sync(url=None)
        return {
            "task_id": self.request.id,
            "status": "completed",
            "result": result
        }
    except Exception as e:
        return {
            "task_id": self.request.id,
            "status": "failed",
            "error": str(e)
        }