"""
Эндпоинты для вызова парсера
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.api.dependencies import get_current_user
from app.tasks import parse_url_task, parse_all_task
from app.parser_service import run_parser_sync

router = APIRouter(prefix="/parser", tags=["parser"])


class ParseRequest(BaseModel):
    """Запрос на парсинг"""
    url: Optional[str] = None


class ParseResponse(BaseModel):
    """Ответ от парсера"""
    task_id: str
    status: str
    message: str
    url: Optional[str] = None


class ParseResultResponse(BaseModel):
    """Результат парсинга"""
    task_id: str
    status: str
    result: Optional[List[Dict[str, Any]]] = None
    error: Optional[str] = None
    created_at: datetime


# ========== СИНХРОННЫЙ ВЫЗОВ (прямой, без очереди) ==========

@router.post("/parse-sync", response_model=List[Dict[str, Any]])
async def parse_sync(
    request: ParseRequest,
    current_user = Depends(get_current_user)
):
    """
    Синхронный вызов парсера (без очереди).
    Ждет завершения парсинга и возвращает результат.
    
    - **url** (опционально): конкретный URL для парсинга
    """
    try:
        result = run_parser_sync(url=request.url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser error: {str(e)}")


# ========== АСИНХРОННЫЙ ВЫЗОВ ЧЕРЕЗ CELERY (очередь) ==========

@router.post("/parse-async", response_model=ParseResponse)
async def parse_async(
    request: ParseRequest,
    current_user = Depends(get_current_user)
):
    """
    Асинхронный вызов парсера через очередь (Celery + Redis).
    Возвращает task_id для отслеживания статуса.
    
    - **url** (опционально): конкретный URL для парсинга
    """
    if request.url:
        task = parse_url_task.delay(request.url)
        return ParseResponse(
            task_id=task.id,
            status="pending",
            message=f"Parser task for URL '{request.url}' has been queued",
            url=request.url
        )
    else:
        task = parse_all_task.delay()
        return ParseResponse(
            task_id=task.id,
            status="pending",
            message="Parser task for all sources has been queued",
            url=None
        )


@router.get("/task/{task_id}", response_model=ParseResultResponse)
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user)
):
    """
    Получение статуса и результата асинхронной задачи
    
    - **task_id**: ID задачи, полученный из /parse-async
    """
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app
    
    task = AsyncResult(task_id, app=celery_app)
    
    if task.ready():
        if task.successful():
            return ParseResultResponse(
                task_id=task_id,
                status="completed",
                result=task.result,
                created_at=datetime.now()
            )
        else:
            return ParseResultResponse(
                task_id=task_id,
                status="failed",
                error=str(task.info),
                created_at=datetime.now()
            )
    else:
        return ParseResultResponse(
            task_id=task_id,
            status="pending",
            result=None,
            created_at=datetime.now()
        )


@router.get("/health")
async def parser_health():
    """Проверка работоспособности парсера"""
    return {"status": "ok", "service": "parser"}