"""Роутер для управления командами"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.services.team_service import TeamService
from app.services.project_service import ProjectService
from app.schemas.team import (
    TeamResponse, TeamDetailResponse,
    CreateTeamRequest, UpdateTeamRequest,
    InviteMemberRequest, UpdateMemberRequest, TeamMemberResponse
)
from app.schemas.pagination import PaginatedResponse, Pagination
from app.models.user import User
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException

router = APIRouter(prefix="/teams", tags=["teams"])


# Эндпоинты для команд в контексте проекта
@router.get("/projects/{project_id}/teams", response_model=PaginatedResponse[TeamResponse])
async def get_project_teams(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Получить команды проекта"""
    # Проверяем существует ли проект
    project_service = ProjectService(db)
    project = await project_service.get(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team_service = TeamService(db)
    teams, total = await team_service.get_project_teams(project_id, page, page_size)
    
    return PaginatedResponse(
        items=teams,
        pagination=Pagination.create(total, page, page_size)
    )


@router.post("/projects/{project_id}/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    project_id: int,
    data: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Создать команду в проекте"""
    team_service = TeamService(db)
    
    try:
        team = await team_service.create_team(project_id, current_user.id, data)
        return team
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить команду по ID"""
    team_service = TeamService(db)
    team = await team_service.get_with_members(team_id)
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: int,
    data: UpdateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить команду (тимлид или владелец проекта)"""
    team_service = TeamService(db)
    
    try:
        team = await team_service.update_team(
            team_id, 
            current_user.id, 
            current_user.role == "ADMIN",
            data
        )
        return team
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить команду (тимлид или владелец проекта)"""
    team_service = TeamService(db)
    
    try:
        deleted = await team_service.delete_team(team_id, current_user.id, current_user.role == "ADMIN")
        if not deleted:
            raise HTTPException(status_code=404, detail="Team not found")
    except ForbiddenException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_team_members(
    team_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить всех участников команды"""
    team_service = TeamService(db)
    
    team = await team_service.get(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    members = await team_service.get_team_members(team_id)
    return members


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def invite_member(
    team_id: int,
    data: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Пригласить пользователя в команду"""
    team_service = TeamService(db)
    
    try:
        member = await team_service.invite_member(team_id, current_user.id, data)
        return member
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member(
    team_id: int,
    user_id: int,
    data: UpdateMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновить статус или роль участника"""
    team_service = TeamService(db)
    
    try:
        member = await team_service.update_member(team_id, user_id, current_user.id, data)
        return member
    except (NotFoundException, ForbiddenException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except ConflictException as e:
        raise HTTPException(status_code=409, detail=e.message)


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    team_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Удалить участника из команды"""
    team_service = TeamService(db)
    
    try:
        deleted = await team_service.remove_member(team_id, user_id, current_user.id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Team or member not found")
    except (ForbiddenException, ConflictException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    
    return None