"""Роутер для административных функций"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user
from app.services.admin_service import AdminService
from app.schemas.admin import AdminStatsResponse
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_platform_stats(
    current_user: User = Depends(get_current_admin_user),  # Только ADMIN
    db: AsyncSession = Depends(get_db)
):
    """Получить общую статистику по платформе (только ADMIN)"""
    admin_service = AdminService(db)
    stats = await admin_service.get_stats()
    return stats