from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, or_, and_
from sqlalchemy.orm import selectinload

from app.services.base import BaseService
from app.models.user import User
from app.models.user_skill import UserSkill
from app.models.skill import Skill
from app.models.project import Project
from app.models.task import Task
from app.models.team_member import TeamMember
from app.models.enums import TaskStatus, MemberStatus
from app.schemas.user import UpdateProfileRequest, AddUserSkillRequest
from app.core.security import hash_password, verify_password
from app.core.exceptions import NotFoundException, ConflictException, UnauthorizedException


class UserService(BaseService[User, None, UpdateProfileRequest]):
    """Сервис для работы с пользователями"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(User, db)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_with_skills(self, user_id: int) -> Optional[User]:
        """Получить пользователя с его навыками"""
        result = await self.db.execute(
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.skills).selectinload(UserSkill.skill))
        )
        return result.scalar_one_or_none()
    
    async def search_users(
        self,
        skill_ids: Optional[List[int]] = None,
        proficiency_level: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[User], int]:
        """Поиск пользователей с фильтрацией"""
        query = select(User).distinct()
        
        # Фильтр по навыкам
        if skill_ids:
            query = query.join(User.skills).where(
                UserSkill.skill_id.in_(skill_ids)
            )
            if proficiency_level:
                query = query.where(UserSkill.proficiency_level == proficiency_level)
        
        # Поиск по имени или bio
        if search:
            query = query.where(
                or_(
                    User.first_name.ilike(f"%{search}%"),
                    User.last_name.ilike(f"%{search}%"),
                    User.bio.ilike(f"%{search}%")
                )
            )
        
        # Сортировка
        order_field = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(order_field.desc())
        else:
            query = query.order_by(order_field.asc())
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        users = list(result.scalars().all())
        
        # Загружаем навыки для каждого пользователя
        for user in users:
            await self.db.refresh(user, attribute_names=["skills"])
        
        return users, total
    
    async def update_profile(self, user_id: int, data: UpdateProfileRequest) -> User:
        """Обновить профиль пользователя"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)
        
        await self.db.flush()
        await self.db.refresh(user)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return user
    
    async def change_password(self, user_id: int, old_password: str, new_password: str) -> None:
        """Сменить пароль пользователя"""
        user = await self.get(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        
        if not verify_password(old_password, user.password_hash):
            raise UnauthorizedException(message="Invalid old password")
        
        user.password_hash = hash_password(new_password)
        await self.db.flush()
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
    
    async def add_skill(self, user_id: int, data: AddUserSkillRequest) -> UserSkill:
        """Добавить навык пользователю"""
        # Проверяем существует ли пользователь
        user = await self.get(user_id)
        if not user:
            raise NotFoundException(message="User not found")
        
        # Проверяем существует ли навык
        skill_result = await self.db.execute(
            select(Skill).where(Skill.id == data.skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        if not skill:
            raise NotFoundException(message="Skill not found")
        
        # Проверяем не добавлен ли уже навык
        existing = await self.db.execute(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == data.skill_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(message="Skill already added to user")
        
        user_skill = UserSkill(
            user_id=user_id,
            skill_id=data.skill_id,
            proficiency_level=data.proficiency_level
        )
        self.db.add(user_skill)
        await self.db.flush()
        await self.db.refresh(user_skill)
        
        # Загружаем связанный навык
        await self.db.refresh(user_skill, attribute_names=["skill"])
        
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return user_skill
    
    async def remove_skill(self, user_id: int, skill_id: int) -> bool:
        """Удалить навык у пользователя"""
        result = await self.db.execute(
            select(UserSkill).where(
                UserSkill.user_id == user_id,
                UserSkill.skill_id == skill_id
            )
        )
        user_skill = result.scalar_one_or_none()
        
        if not user_skill:
            return False
        
        await self.db.delete(user_skill)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True
    
    async def get_user_skills(self, user_id: int) -> List[UserSkill]:
        """Получить все навыки пользователя"""
        result = await self.db.execute(
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .options(selectinload(UserSkill.skill))
        )
        return list(result.scalars().all())
    
    async def get_user_stats(self, user_id: int) -> Dict[str, int]:
        """Получить статистику пользователя"""
        # Количество созданных проектов
        projects_result = await self.db.execute(
            select(func.count()).select_from(Project).where(Project.owner_id == user_id)
        )
        total_projects_owned = projects_result.scalar() or 0
        
        # Количество назначенных задач
        tasks_result = await self.db.execute(
            select(func.count()).select_from(Task).where(Task.assignee_id == user_id)
        )
        total_tasks_assigned = tasks_result.scalar() or 0
        
        # Количество выполненных задач
        completed_result = await self.db.execute(
            select(func.count()).select_from(Task).where(
                Task.assignee_id == user_id,
                Task.status == TaskStatus.DONE
            )
        )
        total_completed_tasks = completed_result.scalar() or 0
        
        # Количество команд (активных участников)
        teams_result = await self.db.execute(
            select(func.count()).select_from(TeamMember).where(
                TeamMember.user_id == user_id,
                TeamMember.status == MemberStatus.ACTIVE
            )
        )
        total_teams = teams_result.scalar() or 0
        
        return {
            "total_projects_owned": total_projects_owned,
            "total_tasks_assigned": total_tasks_assigned,
            "total_teams": total_teams,
            "total_completed_tasks": total_completed_tasks,
        }