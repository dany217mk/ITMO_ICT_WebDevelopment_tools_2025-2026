from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, func
from sqlalchemy.orm import selectinload

from app.services.base import BaseService
from app.models.project import Project
from app.models.project_skill import ProjectSkill
from app.models.skill import Skill
from app.models.team import Team
from app.models.enums import ProjectStatus, SkillImportance
from app.schemas.project import CreateProjectRequest, UpdateProjectRequest, AddProjectSkillRequest
from app.core.exceptions import ConflictException, NotFoundException, ForbiddenException


class ProjectService(BaseService[Project, CreateProjectRequest, UpdateProjectRequest]):
    """Сервис для работы с проектами"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Project, db)
    
    async def get_with_details(self, project_id: int) -> Optional[Project]:
        """Получить проект с навыками и командами"""
        result = await self.db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.required_skills).selectinload(ProjectSkill.skill),
                selectinload(Project.teams)
            )
        )
        return result.scalar_one_or_none()
    
    async def search_projects(
        self,
        status: Optional[ProjectStatus] = None,
        skill_ids: Optional[List[int]] = None,
        owner_id: Optional[int] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Project], int]:
        """Поиск проектов с фильтрацией"""
        query = select(Project).distinct()
        
        # Фильтр по статусу
        if status:
            query = query.where(Project.status == status)
        
        # Фильтр по владельцу
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        
        # Фильтр по навыкам
        if skill_ids:
            query = query.join(Project.required_skills).where(
                ProjectSkill.skill_id.in_(skill_ids)
            )
        
        # Поиск по названию или описанию
        if search:
            query = query.where(
                or_(
                    Project.title.ilike(f"%{search}%"),
                    Project.description.ilike(f"%{search}%")
                )
            )
        
        # Сортировка
        order_field = getattr(Project, sort_by, Project.created_at)
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
        projects = list(result.scalars().all())
        
        return projects, total
    
    async def create_project(self, owner_id: int, data: CreateProjectRequest) -> Project:
        """Создать новый проект"""
        project = Project(
            owner_id=owner_id,
            title=data.title,
            description=data.description,
            deadline=data.deadline,
            status=ProjectStatus.DRAFT
        )
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return project
    
    async def update_project(
        self, 
        project_id: int, 
        user_id: int, 
        is_admin: bool,
        data: UpdateProjectRequest
    ) -> Project:
        """Обновить проект (только владелец или админ)"""
        project = await self.get(project_id)
        if not project:
            raise NotFoundException(message="Project not found")
        
        # Проверка прав
        if project.owner_id != user_id and not is_admin:
            raise ForbiddenException(message="You don't have permission to update this project")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)
        
        await self.db.flush()
        await self.db.refresh(project)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return project
    
    async def delete_project(self, project_id: int, user_id: int, is_admin: bool) -> bool:
        """Удалить проект (только владелец или админ)"""
        project = await self.get(project_id)
        if not project:
            return False
        
        if project.owner_id != user_id and not is_admin:
            raise ForbiddenException(message="You don't have permission to delete this project")
        
        await self.db.delete(project)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True
    
    async def add_skill_to_project(
        self, 
        project_id: int, 
        user_id: int, 
        data: AddProjectSkillRequest
    ) -> ProjectSkill:
        """Добавить навык к проекту"""
        project = await self.get(project_id)
        if not project:
            raise NotFoundException(message="Project not found")
        
        if project.owner_id != user_id:
            raise ForbiddenException(message="Only project owner can add skills")
        
        # Проверяем существует ли навык
        skill_result = await self.db.execute(
            select(Skill).where(Skill.id == data.skill_id)
        )
        skill = skill_result.scalar_one_or_none()
        if not skill:
            raise NotFoundException(message="Skill not found")
        
        # Проверяем не добавлен ли уже
        existing = await self.db.execute(
            select(ProjectSkill).where(
                ProjectSkill.project_id == project_id,
                ProjectSkill.skill_id == data.skill_id
            )
        )
        if existing.scalar_one_or_none():
            raise ConflictException(message="Skill already added to project")
        
        project_skill = ProjectSkill(
            project_id=project_id,
            skill_id=data.skill_id,
            importance=data.importance
        )
        self.db.add(project_skill)
        await self.db.flush()
        await self.db.refresh(project_skill)
        await self.db.refresh(project_skill, attribute_names=["skill"])
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        
        return project_skill
    
    async def remove_skill_from_project(
        self, 
        project_id: int, 
        skill_id: int, 
        user_id: int
    ) -> bool:
        """Удалить навык из проекта"""
        project = await self.get(project_id)
        if not project:
            return False
        
        if project.owner_id != user_id:
            raise ForbiddenException(message="Only project owner can remove skills")
        
        result = await self.db.execute(
            select(ProjectSkill).where(
                ProjectSkill.project_id == project_id,
                ProjectSkill.skill_id == skill_id
            )
        )
        project_skill = result.scalar_one_or_none()
        
        if not project_skill:
            return False
        
        await self.db.delete(project_skill)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True
    
    async def get_project_skills(self, project_id: int) -> List[ProjectSkill]:
        """Получить все навыки проекта"""
        result = await self.db.execute(
            select(ProjectSkill)
            .where(ProjectSkill.project_id == project_id)
            .options(selectinload(ProjectSkill.skill))
        )
        return list(result.scalars().all())