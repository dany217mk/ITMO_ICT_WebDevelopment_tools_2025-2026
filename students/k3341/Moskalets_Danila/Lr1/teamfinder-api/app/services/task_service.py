from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from sqlalchemy.orm import selectinload

from app.services.base import BaseService
from app.models.task import Task
from app.models.project import Project
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority
from app.schemas.task import CreateTaskRequest, UpdateTaskRequest
from app.core.exceptions import NotFoundException, ForbiddenException


class TaskService(BaseService[Task, CreateTaskRequest, UpdateTaskRequest]):
    """Сервис для работы с задачами"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Task, db)
    
    async def get_with_assignee(self, task_id: int) -> Optional[Task]:
        """Получить задачу с исполнителем"""
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.assignee))
        )
        return result.scalar_one_or_none()
    
    async def get_project_tasks(
        self,
        project_id: int,
        status: Optional[TaskStatus] = None,
        assignee_id: Optional[int] = None,
        priority: Optional[TaskPriority] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Task], int]:
        """Получить задачи проекта с фильтрацией"""
        query = select(Task).where(Task.project_id == project_id)
        
        # Фильтры
        if status:
            query = query.where(Task.status == status)
        
        if assignee_id:
            query = query.where(Task.assignee_id == assignee_id)
        
        if priority:
            query = query.where(Task.priority == priority)
        
        # Сортировка
        if sort_by == "priority":
            # Сортировка по приоритету (CRITICAL > HIGH > MEDIUM > LOW)
            priority_order = {
                TaskPriority.CRITICAL: 4,
                TaskPriority.HIGH: 3,
                TaskPriority.MEDIUM: 2,
                TaskPriority.LOW: 1
            }
            priority_case = case(
                priority_order,
                value=Task.priority
            )
            if sort_order == "desc":
                query = query.order_by(priority_case.desc())
            else:
                query = query.order_by(priority_case)
        else:
            order_field = getattr(Task, sort_by, Task.created_at)
            if sort_order == "desc":
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field)
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        tasks = list(result.scalars().all())
        
        return tasks, total
    
    async def create_task(
        self,
        project_id: int,
        created_by_id: int,
        data: CreateTaskRequest
    ) -> Task:
        """Создать задачу в проекте"""
        # Проверяем существует ли проект
        project_result = await self.db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = project_result.scalar_one_or_none()
        if not project:
            raise NotFoundException(message="Project not found")
        
        task = Task(
            project_id=project_id,
            title=data.title,
            description=data.description,
            assignee_id=data.assignee_id,
            priority=data.priority,
            due_date=data.due_date,
            status=TaskStatus.TODO
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        
        return task
    
    async def update_task(
        self,
        task_id: int,
        user_id: int,
        is_admin: bool,
        data: UpdateTaskRequest
    ) -> Task:
        """Обновить задачу"""
        task = await self.get_with_assignee(task_id)
        if not task:
            raise NotFoundException(message="Task not found")
        
        # Проверяем права (админ, исполнитель или владелец проекта)
        has_permission = is_admin
        
        if not has_permission:
            # Проверяем является ли пользователь исполнителем
            if task.assignee_id == user_id:
                has_permission = True
            
            # Проверяем является ли пользователь владельцем проекта
            if not has_permission:
                project_result = await self.db.execute(
                    select(Project).where(Project.id == task.project_id)
                )
                project = project_result.scalar_one_or_none()
                if project and project.owner_id == user_id:
                    has_permission = True
        
        if not has_permission:
            raise ForbiddenException(message="You don't have permission to update this task")
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(task, key, value)
        
        await self.db.flush()
        await self.db.refresh(task)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        
        return task
    
    async def delete_task(
        self,
        task_id: int,
        user_id: int,
        is_admin: bool
    ) -> bool:
        """Удалить задачу"""
        task = await self.get(task_id)
        if not task:
            return False
        
        # Проверяем права (админ или владелец проекта)
        has_permission = is_admin
        
        if not has_permission:
            project_result = await self.db.execute(
                select(Project).where(Project.id == task.project_id)
            )
            project = project_result.scalar_one_or_none()
            if project and project.owner_id == user_id:
                has_permission = True
        
        if not has_permission:
            raise ForbiddenException(message="You don't have permission to delete this task")
        
        await self.db.delete(task)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return True
    
    async def get_my_tasks(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[Task], int]:
        """Получить задачи назначенные пользователю"""
        query = select(Task).where(Task.assignee_id == user_id)
        
        if status:
            query = query.where(Task.status == status)
        
        query = query.order_by(Task.created_at.desc())
        
        # Подсчет общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0
        
        # Пагинация
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        tasks = list(result.scalars().all())
        
        return tasks, total