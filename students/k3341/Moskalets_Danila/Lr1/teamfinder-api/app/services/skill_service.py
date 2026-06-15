from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.services.base import BaseService
from app.models.skill import Skill
from app.schemas.skill import CreateSkillRequest
from app.core.exceptions import ConflictException, NotFoundException


class SkillService(BaseService[Skill, CreateSkillRequest, CreateSkillRequest]):
    """Сервис для работы со справочником навыков"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(Skill, db)
    
    async def get_by_name(self, name: str) -> Optional[Skill]:
        """Получить навык по названию"""
        result = await self.db.execute(
            select(Skill).where(Skill.name == name)
        )
        return result.scalar_one_or_none()
    
    async def search_skills(
        self,
        category: Optional[str] = None,
        search: Optional[str] = None
    ) -> List[Skill]:
        """Поиск навыков по категории или названию"""
        query = select(Skill)
        
        if category:
            query = query.where(Skill.category == category)
        
        if search:
            query = query.where(Skill.name.ilike(f"%{search}%"))
        
        query = query.order_by(Skill.name)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def create_skill(self, data: CreateSkillRequest) -> Skill:
        """Создать новый навык (только для админа)"""
        # Проверяем существует ли навык с таким названием
        existing = await self.get_by_name(data.name)
        if existing:
            raise ConflictException(message=f"Skill '{data.name}' already exists")
        
        skill = Skill(
            name=data.name,
            category=data.category
        )
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        await self.db.commit()  # <--- ДОБАВИТЬ COMMIT!
        return skill