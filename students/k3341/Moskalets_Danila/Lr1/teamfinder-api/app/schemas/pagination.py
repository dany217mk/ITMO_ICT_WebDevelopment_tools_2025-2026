from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List
from math import ceil

T = TypeVar("T")


class Pagination(BaseModel):
    """Параметры пагинации"""
    total: int = Field(..., description="Общее количество записей", example=150)
    page: int = Field(..., description="Текущая страница (1-based)", ge=1, example=2)
    page_size: int = Field(..., description="Размер страницы", ge=1, le=100, example=20)
    total_pages: int = Field(..., description="Всего страниц", example=8)
    
    @classmethod
    def create(cls, total: int, page: int, page_size: int) -> "Pagination":
        return cls(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0
        )


class PaginatedResponse(BaseModel, Generic[T]):
    """Обертка для пагинированного ответа"""
    items: List[T]
    pagination: Pagination