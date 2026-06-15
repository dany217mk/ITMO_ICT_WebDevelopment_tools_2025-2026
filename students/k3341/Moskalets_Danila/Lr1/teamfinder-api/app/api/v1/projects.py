"""Роутер для управления проектами"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_admin_user
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectResponse, ProjectDetailResponse,
    CreateProjectRequest, UpdateProjectRequest,
    AddProjectSkillRequest, ProjectSkillResponse,
    ProjectStatus
)
from app.schemas.pagination import PaginatedResponse, Pagination
from app.models.user import User
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectResponse])
async def search_projects(
    status: Optional[ProjectStatus] = Query(None, description="Статус проекта"),
    skill_ids: Optional[List[int]] = Query(None, description="Фильтр по ID навыков"),
    owner_id: Optional[int] = Query(None, description="Фильтр по владельцу"),
    search: Optional[str] = Query(None, description="Поиск по названию или описанию"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Направление сортировки"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Поиск и фильтрация проектов"""
    service = ProjectService(db)
    
    projects, total = await service.search_projects(
        status=status,
        skill_ids=skill_ids,
        owner_id=owner_id,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse(
        items=projects,
        pagination=Pagination.create(total, page, page_size)
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: CreateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать проект"""
    service = ProjectService(db)
    project = await service.create_project(current_user.id, data)
    return project


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить проект по ID"""
    service = ProjectService(db)
    project = await service.get_with_details(project_id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: UpdateProjectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить проект (только владелец)"""
    service = ProjectService(db)
    
    try:
        project = await service.update_project(
            project_id, 
            current_user.id, 
            current_user.role == "ADMIN",
            data
        )
        return project
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить проект (только владелец или ADMIN)"""
    service = ProjectService(db)
    
    try:
        deleted = await service.delete_project(
            project_id, 
            current_user.id, 
            current_user.role == "ADMIN"
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Project not found")
    except ForbiddenException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None


@router.get("/{project_id}/skills", response_model=List[ProjectSkillResponse])
async def get_project_skills(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить все требуемые навыки проекта"""
    service = ProjectService(db)
    
    project = await service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    skills = await service.get_project_skills(project_id)
    return skills


@router.post("/{project_id}/skills", response_model=ProjectSkillResponse, status_code=status.HTTP_201_CREATED)
async def add_project_skill(
    project_id: int,
    data: AddProjectSkillRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Добавить требуемый навык к проекту"""
    service = ProjectService(db)
    
    try:
        project_skill = await service.add_skill_to_project(project_id, current_user.id, data)
        return project_skill
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.delete("/{project_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_project_skill(
    project_id: int,
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить навык из проекта"""
    service = ProjectService(db)
    
    try:
        deleted = await service.remove_skill_from_project(project_id, skill_id, current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Project skill not found")
    except ForbiddenException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None