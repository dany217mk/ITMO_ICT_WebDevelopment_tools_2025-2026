from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "TeamFinder API"
    }


@router.get("/ready")
async def readiness_check():
    """Проверка готовности сервиса"""
    return {"status": "ready", "message": "API is ready to accept requests"}