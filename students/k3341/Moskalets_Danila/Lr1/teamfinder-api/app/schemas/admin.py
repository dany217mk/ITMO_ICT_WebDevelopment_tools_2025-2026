from pydantic import BaseModel
from typing import Dict, List


class PopularSkill(BaseModel):
    """Популярный навык"""
    skill_name: str
    count: int


class AdminStatsResponse(BaseModel):
    """Статистика для администратора"""
    total_users: int
    total_projects: int
    total_active_projects: int
    total_teams: int
    total_tasks: int
    total_tasks_completed: int
    popular_skills: List[PopularSkill] = []
    projects_by_status: Dict[str, int] = {}