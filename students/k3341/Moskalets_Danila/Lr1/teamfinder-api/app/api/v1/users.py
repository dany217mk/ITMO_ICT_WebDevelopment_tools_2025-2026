"""Роутер для управления пользователями"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.core.exceptions import NotFoundException, ConflictException, UnauthorizedException
from app.api.dependencies import get_current_user, get_current_admin_user
from app.services.user_service import UserService
from app.schemas.user import (
    UserResponse, UserDetailResponse, UserStatsResponse,
    UpdateProfileRequest, ChangePasswordRequest,
    AddUserSkillRequest, UserSkillResponse
)
from app.schemas.pagination import PaginatedResponse, Pagination
from app.models.user import User
from app.models.enums import ProficiencyLevel

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=PaginatedResponse[UserResponse])
async def search_users(
    skill_ids: Optional[List[int]] = Query(None, description="Фильтр по ID навыков"),
    proficiency_level: Optional[ProficiencyLevel] = Query(None, description="Уровень владения навыком"),
    search: Optional[str] = Query(None, description="Поиск по имени или bio"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Направление сортировки"),
    page: int = Query(1, ge=1, description="Номер страницы"),
    page_size: int = Query(20, ge=1, le=100, description="Количество на странице"),
    db: AsyncSession = Depends(get_db)
):
    """Поиск и фильтрация пользователей"""
    service = UserService(db)
    
    users, total = await service.search_users(
        skill_ids=skill_ids,
        proficiency_level=proficiency_level,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse(
        items=users,
        pagination=Pagination.create(total, page, page_size)
    )


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_profile(
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить профиль пользователя с его навыками"""
    service = UserService(db)
    user = await service.get_with_skills(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить свой профиль"""
    service = UserService(db)
    user = await service.update_profile(current_user.id, data)
    return user


@router.post("/me/change-password")
async def change_my_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Смена пароля текущего пользователя"""
    service = UserService(db)
    
    try:
        await service.change_password(
            current_user.id,
            data.old_password,
            data.new_password
        )
        return {"message": "Password changed successfully"}
    except UnauthorizedException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику текущего пользователя"""
    service = UserService(db)
    stats = await service.get_user_stats(current_user.id)
    return stats


@router.get("/me/skills", response_model=List[UserSkillResponse])
async def get_my_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить навыки текущего пользователя"""
    service = UserService(db)
    skills = await service.get_user_skills(current_user.id)
    return skills


@router.post("/me/skills", response_model=UserSkillResponse, status_code=status.HTTP_201_CREATED)
async def add_my_skill(
    data: AddUserSkillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить навык текущему пользователю"""
    service = UserService(db)
    
    try:
        user_skill = await service.add_skill(current_user.id, data)
        return user_skill
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.delete("/me/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_my_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить навык у текущего пользователя"""
    service = UserService(db)
    deleted = await service.remove_skill(current_user.id, skill_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="User skill not found")
    
    return None