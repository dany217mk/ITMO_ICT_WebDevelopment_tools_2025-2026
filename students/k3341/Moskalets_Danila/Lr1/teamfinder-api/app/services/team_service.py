from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.services.base import BaseService
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.project import Project
from app.models.user import User
from app.models.enums import TeamRole, MemberStatus
from app.schemas.team import CreateTeamRequest, UpdateTeamRequest, InviteMemberRequest, UpdateMemberRequest
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException


class TeamService(BaseService[Team, CreateTeamRequest, UpdateTeamRequest]):
    """Сервис для работы с командами"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Team, db)
    
    async def get_with_members(self, team_id: int) -> Optional[Team]:
        """Получить команду с участниками"""
        result = await self.db.execute(
            select(Team)
            .where(Team.id == team_id)
            .options(selectinload(Team.members).selectinload(TeamMember.user))
        )
        return result.scalar_one_or_none()
    
    async def get_project_teams(
        self, 
        project_id: int, 
        page: int = 1, 
        page_size: int = 20
    ) -> tuple[List[Team], int]:
        """Получить все команды проекта с пагинацией"""
        query = select(Team).where(Team.project_id == project_id)
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(Team).where(Team.project_id == project_id)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        teams = list(result.scalars().all())
        
        return teams, total
    
    async def create_team(
        self, 
        project_id: int, 
        created_by: int, 
        data: CreateTeamRequest
    ) -> Team:
        """Создать команду в проекте"""
        # Проверяем существует ли проект
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise NotFoundException(message="Project not found")
        
        team = Team(
            project_id=project_id,
            created_by=created_by,
            name=data.name,
            description=data.description
        )
        self.db.add(team)
        await self.db.flush()
        await self.db.refresh(team)
        
        # Создатель автоматически становится LEAD-ом команды
        team_member = TeamMember(
            team_id=team.id,
            user_id=created_by,
            role_in_team=TeamRole.LEAD,
            status=MemberStatus.ACTIVE
        )
        self.db.add(team_member)
        await self.db.flush()
        
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return team
    
    async def update_team(
        self, 
        team_id: int, 
        user_id: int, 
        is_admin: bool,
        data: UpdateTeamRequest
    ) -> Team:
        """Обновить команду (тимлид или владелец проекта или админ)"""
        team = await self.get_with_members(team_id)
        if not team:
            raise NotFoundException(message="Team not found")
        
        # Проверяем права
        has_permission = is_admin
        if not has_permission:
            # Проверяем является ли пользователь тимлидом
            for member in team.members:
                if member.user_id == user_id and member.role_in_team == TeamRole.LEAD:
                    has_permission = True
                    break
            
            # Или владельцем проекта
            if not has_permission:
                project_result = await self.db.execute(
                    select(Project).where(Project.id == team.project_id)
                )
                project = project_result.scalar_one_or_none()
                if project and project.owner_id == user_id:
                    has_permission = True
        
        if not has_permission:
            raise ForbiddenException(message="You don't have permission to update this team")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(team, key, value)
        
        await self.db.flush()
        await self.db.refresh(team)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return team
    
    async def delete_team(self, team_id: int, user_id: int, is_admin: bool) -> bool:
        """Удалить команду"""
        team = await self.get(team_id)
        if not team:
            return False
        
        # Проверка прав (админ или владелец проекта)
        has_permission = is_admin
        if not has_permission:
            project_result = await self.db.execute(
                select(Project).where(Project.id == team.project_id)
            )
            project = project_result.scalar_one_or_none()
            if project and project.owner_id == user_id:
                has_permission = True
        
        if not has_permission:
            raise ForbiddenException(message="You don't have permission to delete this team")
        
        await self.db.delete(team)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True
    
    async def get_team_members(self, team_id: int) -> List[TeamMember]:
        """Получить всех участников команды"""
        result = await self.db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .options(selectinload(TeamMember.user))
        )
        return list(result.scalars().all())
    
    async def invite_member(
        self, 
        team_id: int, 
        current_user_id: int, 
        data: InviteMemberRequest
    ) -> TeamMember:
        """Пригласить пользователя в команду"""
        team = await self.get_with_members(team_id)
        if not team:
            raise NotFoundException(message="Team not found")
        
        # Проверяем права (тимлид или владелец проекта)
        is_lead = any(
            m.user_id == current_user_id and m.role_in_team == TeamRole.LEAD 
            for m in team.members
        )
        is_owner = False
        if not is_lead:
            project_result = await self.db.execute(
                select(Project).where(Project.id == team.project_id)
            )
            project = project_result.scalar_one_or_none()
            is_owner = project and project.owner_id == current_user_id
        
        if not is_lead and not is_owner:
            raise ForbiddenException(message="Only team lead or project owner can invite members")
        
        # Проверяем существует ли пользователь
        user_result = await self.db.execute(
            select(User).where(User.id == data.user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            raise NotFoundException(message="User not found")
        
        # Проверяем не состоит ли уже в команде
        existing = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == data.user_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(message="User already in team")
        
        team_member = TeamMember(
            team_id=team_id,
            user_id=data.user_id,
            role_in_team=data.role_in_team,
            status=MemberStatus.INVITED
        )
        self.db.add(team_member)
        await self.db.flush()
        await self.db.refresh(team_member)
        await self.db.refresh(team_member, attribute_names=["user"])
        
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return team_member
    
    async def update_member(
        self, 
        team_id: int, 
        user_id: int, 
        current_user_id: int, 
        data: UpdateMemberRequest
    ) -> TeamMember:
        """Обновить статус или роль участника"""
        team = await self.get_with_members(team_id)
        if not team:
            raise NotFoundException(message="Team not found")
        
        # Находим участника
        member = None
        for m in team.members:
            if m.user_id == user_id:
                member = m
                break
        
        if not member:
            raise NotFoundException(message="Team member not found")
        
        # Проверяем права
        is_lead = any(
            m.user_id == current_user_id and m.role_in_team == TeamRole.LEAD 
            for m in team.members
        )
        is_self = current_user_id == user_id
        
        if not is_lead and not is_self:
            raise ForbiddenException(message="Only team lead can update members")
        
        # Нельзя понизить последнего LEAD-а
        if data.role_in_team and data.role_in_team != TeamRole.LEAD:
            leads_count = sum(1 for m in team.members if m.role_in_team == TeamRole.LEAD)
            if member.role_in_team == TeamRole.LEAD and leads_count == 1:
                raise ConflictException(message="Cannot remove the last team lead")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(member, key, value)
        
        await self.db.flush()
        await self.db.refresh(member)
        await self.db.refresh(member, attribute_names=["user"])
        
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return member
    
    async def remove_member(
        self, 
        team_id: int, 
        user_id: int, 
        current_user_id: int
    ) -> bool:
        """Удалить участника из команды"""
        team = await self.get_with_members(team_id)
        if not team:
            return False
        
        # Находим участника
        member = None
        for m in team.members:
            if m.user_id == user_id:
                member = m
                break
        
        if not member:
            return False
        
        # Проверяем права
        is_lead = any(
            m.user_id == current_user_id and m.role_in_team == TeamRole.LEAD 
            for m in team.members
        )
        is_self = current_user_id == user_id
        
        if not is_lead and not is_self:
            raise ForbiddenException(message="Only team lead can remove members")
        
        # Нельзя удалить последнего LEAD-а
        if member.role_in_team == TeamRole.LEAD:
            leads_count = sum(1 for m in team.members if m.role_in_team == TeamRole.LEAD)
            if leads_count == 1:
                raise ConflictException(message="Cannot remove the last team lead")
        
        await self.db.delete(member)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True