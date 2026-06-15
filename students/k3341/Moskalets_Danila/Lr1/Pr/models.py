from enum import Enum
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime

# ============= Перечисления =============
class RaceType(str, Enum):
    director = "director"
    worker = "worker"
    junior = "junior"

# ============= Ассоциативная таблица (многие-ко-многим) =============
class SkillWarriorLink(SQLModel, table=True):
    """Связь между воинами и умениями"""
    skill_id: int = Field(
        default=None,
        foreign_key="skill.id",
        primary_key=True
    )
    warrior_id: int = Field(
        default=None,
        foreign_key="warrior.id",
        primary_key=True
    )
    created_at: datetime = Field(default_factory=datetime.now)

# ============= Модель умения =============
class SkillDefault(SQLModel):
    """Базовая модель умения (для создания/обновления)"""
    name: str
    description: Optional[str] = ""

class Skill(SkillDefault, table=True):
    """Модель умения для БД"""
    id: int = Field(default=None, primary_key=True)
    warriors: Optional[List["Warrior"]] = Relationship(
        back_populates="skills",
        link_model=SkillWarriorLink,
        sa_relationship_kwargs={"cascade": "all, delete"}
    )

# ============= Модель профессии =============
class ProfessionDefault(SQLModel):
    """Базовая модель профессии"""
    title: str
    description: str

class Profession(ProfessionDefault, table=True):
    """Модель профессии для БД"""
    id: int = Field(default=None, primary_key=True)
    warriors_prof: List["Warrior"] = Relationship(
        back_populates="profession",
        sa_relationship_kwargs={"cascade": "all, delete"}
    )

# ============= Модель воина =============
class WarriorDefault(SQLModel):
    """Базовая модель воина (без id и связей many-to-many)"""
    race: RaceType
    name: str
    level: int
    profession_id: Optional[int] = Field(default=None, foreign_key="profession.id")

class Warrior(WarriorDefault, table=True):
    """Модель воина для БД"""
    id: int = Field(default=None, primary_key=True)
    profession: Optional[Profession] = Relationship(back_populates="warriors_prof")
    skills: Optional[List[Skill]] = Relationship(
        back_populates="warriors",
        link_model=SkillWarriorLink
    )

# ============= Модели для response с вложенными объектами =============
class WarriorWithProfession(WarriorDefault):
    """Воин с вложенной профессией"""
    profession: Optional[Profession] = None

class WarriorWithSkills(WarriorDefault):
    """Воин с вложенными умениями"""
    skills: Optional[List[Skill]] = []

class WarriorFull(WarriorDefault):
    """Воин со всеми связями"""
    profession: Optional[Profession] = None
    skills: Optional[List[Skill]] = []