"""Роутер для управления справочником навыков"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.dependencies import get_current_admin_user, get_current_user
from app.services.skill_service import SkillService
from app.schemas.skill import SkillResponse, CreateSkillRequest
from app.models.user import User
from app.core.exceptions import ConflictException

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("", response_model=List[SkillResponse])
async def get_skills(
    category: Optional[str] = Query(None, description="Фильтр по категории"),
    search: Optional[str] = Query(None, description="Поиск по названию навыка"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список всех навыков"""
    service = SkillService(db)
    skills = await service.search_skills(category=category, search=search)
    return skills


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    data: CreateSkillRequest,
    current_user: User = Depends(get_current_admin_user),  # Только ADMIN
    db: AsyncSession = Depends(get_db)
):
    """Создать навык (только ADMIN)"""
    service = SkillService(db)
    
    try:
        skill = await service.create_skill(data)
        return skill
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)