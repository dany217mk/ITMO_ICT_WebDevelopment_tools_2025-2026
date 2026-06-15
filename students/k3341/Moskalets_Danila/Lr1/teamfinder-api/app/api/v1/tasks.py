"""Роутер для управления задачами"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.task_service import TaskService
from app.services.project_service import ProjectService
from app.schemas.task import (
    TaskResponse,
    CreateTaskRequest, UpdateTaskRequest,
    TaskStatus, TaskPriority
)
from app.schemas.pagination import PaginatedResponse, Pagination
from app.models.user import User
from app.core.exceptions import NotFoundException, ForbiddenException

router = APIRouter(prefix="/tasks", tags=["tasks"])


# Эндпоинты для задач в контексте проекта
@router.get("/projects/{project_id}/tasks", response_model=PaginatedResponse[TaskResponse])
async def get_project_tasks(
    project_id: int,
    status: Optional[TaskStatus] = Query(None, description="Статус задачи"),
    assignee_id: Optional[int] = Query(None, description="ID исполнителя"),
    priority: Optional[TaskPriority] = Query(None, description="Приоритет"),
    sort_by: str = Query("created_at", description="Поле для сортировки"),
    sort_order: str = Query("desc", description="Направление сортировки"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получить задачи проекта"""
    # Проверяем существует ли проект
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    task_service = TaskService(db)
    tasks, total = await task_service.get_project_tasks(
        project_id=project_id,
        status=status,
        assignee_id=assignee_id,
        priority=priority,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse(
        items=tasks,
        pagination=Pagination.create(total, page, page_size)
    )


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: int,
    data: CreateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать задачу в проекте"""
    task_service = TaskService(db)
    
    try:
        task = await task_service.create_task(project_id, current_user.id, data)
        return task
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/my-tasks", response_model=PaginatedResponse[TaskResponse])
async def get_my_tasks(
    status: Optional[TaskStatus] = Query(None, description="Статус задачи"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить задачи текущего пользователя"""
    task_service = TaskService(db)
    tasks, total = await task_service.get_my_tasks(
        user_id=current_user.id,
        status=status,
        page=page,
        page_size=page_size
    )
    
    return PaginatedResponse(
        items=tasks,
        pagination=Pagination.create(total, page, page_size)
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить задачу по ID"""
    task_service = TaskService(db)
    task = await task_service.get_with_assignee(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    data: UpdateTaskRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить задачу"""
    task_service = TaskService(db)
    
    try:
        task = await task_service.update_task(
            task_id,
            current_user.id,
            current_user.role == "ADMIN",
            data
        )
        return task
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить задачу"""
    task_service = TaskService(db)
    
    try:
        deleted = await task_service.delete_task(
            task_id,
            current_user.id,
            current_user.role == "ADMIN"
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")
    except ForbiddenException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None