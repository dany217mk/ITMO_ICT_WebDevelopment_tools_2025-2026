"""Базовый CRUD сервис с общими методами"""
from typing import Generic, TypeVar, Type, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import Select

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Базовый класс для сервисов с CRUD операциями"""
    
    def __init__(self, model: Type[ModelType], db: AsyncSession):
        self.model = model
        self.db = db
    
    async def get(self, id: int) -> Optional[ModelType]:
        """Получить запись по ID"""
        result = await self.db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_desc: bool = True
    ) -> List[ModelType]:
        """Получить список записей с пагинацией и фильтрацией"""
        query = select(self.model)
        
        # Применяем фильтры
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        # Сортировка
        if order_by and hasattr(self.model, order_by):
            order_field = getattr(self.model, order_by)
            if order_desc:
                query = query.order_by(order_field.desc())
            else:
                query = query.order_by(order_field.asc())
        
        # Пагинация
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Получить количество записей"""
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key) and value is not None:
                    query = query.where(getattr(self.model, key) == value)
        
        result = await self.db.execute(query)
        return result.scalar() or 0
    
    async def create(self, data: CreateSchemaType) -> ModelType:
        """Создать новую запись"""
        obj = self.model(**data.model_dump())
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj
    
    async def update(self, id: int, data: UpdateSchemaType) -> Optional[ModelType]:
        """Обновить запись"""
        obj = await self.get(id)
        if not obj:
            return None
        
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        
        await self.db.flush()
        await self.db.refresh(obj)
        return obj
    
    async def delete(self, id: int) -> bool:
        """Удалить запись"""
        result = await self.db.execute(
            delete(self.model).where(self.model.id == id)
        )
        return result.rowcount > 0