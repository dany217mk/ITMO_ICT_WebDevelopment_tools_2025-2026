from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.sql import label

from app.models.user import User
from app.models.project import Project
from app.models.team import Team
from app.models.task import Task
from app.models.user_skill import UserSkill
from app.models.skill import Skill
from app.models.enums import ProjectStatus, TaskStatus
from app.schemas.admin import AdminStatsResponse, PopularSkill


class AdminService:
    """Сервис для административной статистики"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_stats(self) -> AdminStatsResponse:
        """Получить общую статистику по платформе"""
        
        # Общее количество пользователей
        total_users_result = await self.db.execute(
            select(func.count()).select_from(User)
        )
        total_users = total_users_result.scalar() or 0
        
        # Общее количество проектов
        total_projects_result = await self.db.execute(
            select(func.count()).select_from(Project)
        )
        total_projects = total_projects_result.scalar() or 0
        
        # Количество активных проектов (OPEN и IN_PROGRESS)
        active_projects_result = await self.db.execute(
            select(func.count()).select_from(Project).where(
                Project.status.in_([ProjectStatus.OPEN, ProjectStatus.IN_PROGRESS])
            )
        )
        total_active_projects = active_projects_result.scalar() or 0
        
        # Общее количество команд
        total_teams_result = await self.db.execute(
            select(func.count()).select_from(Team)
        )
        total_teams = total_teams_result.scalar() or 0
        
        # Общее количество задач
        total_tasks_result = await self.db.execute(
            select(func.count()).select_from(Task)
        )
        total_tasks = total_tasks_result.scalar() or 0
        
        # Количество выполненных задач
        completed_tasks_result = await self.db.execute(
            select(func.count()).select_from(Task).where(Task.status == TaskStatus.DONE)
        )
        total_tasks_completed = completed_tasks_result.scalar() or 0
        
        # Топ-5 популярных навыков
        popular_skills_result = await self.db.execute(
            select(
                Skill.name.label("skill_name"),
                func.count(UserSkill.skill_id).label("count")
            )
            .join(UserSkill, Skill.id == UserSkill.skill_id)
            .group_by(Skill.id, Skill.name)
            .order_by(func.count(UserSkill.skill_id).desc())
            .limit(5)
        )
        popular_skills = [
            PopularSkill(skill_name=row.skill_name, count=row.count)
            for row in popular_skills_result
        ]
        
        # Распределение проектов по статусам
        projects_by_status_result = await self.db.execute(
            select(
                Project.status,
                func.count().label("count")
            )
            .group_by(Project.status)
        )
        projects_by_status = {
            status.value: count
            for status, count in projects_by_status_result
        }
        
        return AdminStatsResponse(
            total_users=total_users,
            total_projects=total_projects,
            total_active_projects=total_active_projects,
            total_teams=total_teams,
            total_tasks=total_tasks,
            total_tasks_completed=total_tasks_completed,
            popular_skills=popular_skills,
            projects_by_status=projects_by_status
        )