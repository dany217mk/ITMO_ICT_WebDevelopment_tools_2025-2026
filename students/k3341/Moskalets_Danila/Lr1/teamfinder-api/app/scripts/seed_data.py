"""
Скрипт для заполнения базы данных тестовыми данными.
Запуск: poetry run python -m app.scripts.seed_data
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import List

from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.models.skill import Skill
from app.models.user_skill import UserSkill
from app.models.project import Project
from app.models.project_skill import ProjectSkill
from app.models.team import Team
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.enums import (
    UserRole,
    ProficiencyLevel,
    ProjectStatus,
    TeamRole,
    MemberStatus,
    SkillImportance,
    TaskStatus,
    TaskPriority,
)

fake = Faker()
Faker.seed(42)


# Предопределенные навыки
SKILLS_DATA = [
    ("Python", "Programming"),
    ("JavaScript", "Programming"),
    ("TypeScript", "Programming"),
    ("Java", "Programming"),
    ("Go", "Programming"),
    ("Rust", "Programming"),
    ("C++", "Programming"),
    ("React", "Frontend"),
    ("Vue.js", "Frontend"),
    ("Angular", "Frontend"),
    ("Next.js", "Frontend"),
    ("FastAPI", "Backend"),
    ("Django", "Backend"),
    ("Spring Boot", "Backend"),
    ("Node.js", "Backend"),
    ("PostgreSQL", "Database"),
    ("MongoDB", "Database"),
    ("Redis", "Database"),
    ("Docker", "DevOps"),
    ("Kubernetes", "DevOps"),
    ("AWS", "DevOps"),
    ("Git", "Tools"),
    ("Figma", "Design"),
    ("UI/UX Design", "Design"),
    ("Project Management", "Management"),
    ("Agile", "Management"),
    ("Scrum", "Management"),
    ("Data Science", "Data"),
    ("Machine Learning", "Data"),
    ("TensorFlow", "Data"),
    ("PyTorch", "Data"),
]


async def clear_database(db: AsyncSession):
    """Очистка базы данных"""
    print("🧹 Очистка базы данных...")
    
    await db.execute(text("TRUNCATE TABLE tasks CASCADE"))
    await db.execute(text("TRUNCATE TABLE team_members CASCADE"))
    await db.execute(text("TRUNCATE TABLE teams CASCADE"))
    await db.execute(text("TRUNCATE TABLE project_skills CASCADE"))
    await db.execute(text("TRUNCATE TABLE projects CASCADE"))
    await db.execute(text("TRUNCATE TABLE user_skills CASCADE"))
    await db.execute(text("TRUNCATE TABLE refresh_tokens CASCADE"))
    await db.execute(text("TRUNCATE TABLE users CASCADE"))
    await db.execute(text("TRUNCATE TABLE skills CASCADE"))
    
    await db.commit()
    print("   ✅ База данных очищена")


async def seed_skills(db: AsyncSession) -> List[Skill]:
    """Создание справочника навыков"""
    print("🌱 Создание навыков...")
    skills = []
    
    for name, category in SKILLS_DATA:
        skill = Skill(name=name, category=category)
        db.add(skill)
        skills.append(skill)
    
    await db.flush()
    print(f"   ✅ Создано {len(skills)} навыков")
    return skills


async def seed_users(db: AsyncSession, count: int = 40) -> List[User]:
    """Создание пользователей"""
    print(f"👤 Создание {count} пользователей...")
    users = []
    
    # Админ
    admin = User(
        first_name="Admin",
        last_name="User",
        email="admin@example.com",
        password_hash=hash_password("admin123"),
        role=UserRole.ADMIN,
        is_verified=True,
        bio="System administrator"
    )
    db.add(admin)
    users.append(admin)
    
    # Обычные пользователи
    for i in range(count):
        user = User(
            first_name=fake.first_name(),
            last_name=fake.last_name(),
            email=fake.unique.email(),
            password_hash=hash_password("password123"),
            role=UserRole.USER,
            is_verified=random.choice([True, False]),
            bio=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
            avatar_url=fake.image_url() if random.random() > 0.5 else None,
        )
        db.add(user)
        users.append(user)
    
    await db.flush()
    
    # Выводим несколько email для тестирования
    print(f"   ✅ Создано {len(users)} пользователей")
    print("   📧 Примеры email для входа (пароль: password123):")
    for user in users[1:5]:  # Показываем первых 4 обычных пользователей
        print(f"      - {user.email}")
    
    return users


async def seed_user_skills(db: AsyncSession, users: List[User], skills: List[Skill]):
    """Назначение навыков пользователям"""
    print("🎯 Назначение навыков пользователям...")
    count = 0
    levels = list(ProficiencyLevel)
    
    for user in users:
        if user.role == UserRole.ADMIN:
            continue
        num = random.randint(1, 5)
        selected_skills = random.sample(skills, min(num, len(skills)))
        for skill in selected_skills:
            user_skill = UserSkill(
                user_id=user.id,
                skill_id=skill.id,
                proficiency_level=random.choice(levels)
            )
            db.add(user_skill)
            count += 1
    
    await db.flush()
    print(f"   ✅ Назначено {count} навыков")


async def seed_projects(db: AsyncSession, users: List[User], count: int = 35) -> List[Project]:
    """Создание проектов"""
    print(f"📁 Создание {count} проектов...")
    projects = []
    statuses = list(ProjectStatus)
    regular_users = [u for u in users if u.role == UserRole.USER]
    
    for i in range(count):
        # Генерируем случайную дату в пределах последних 6 месяцев
        days_ago = random.randint(0, 180)
        created_at = datetime.now() - timedelta(days=days_ago)
        
        project = Project(
            owner_id=random.choice(regular_users).id,
            title=fake.catch_phrase(),
            description=fake.text(max_nb_chars=500),
            status=random.choice(statuses),
            deadline=random.choice([None, datetime.now().date() + timedelta(days=random.randint(1, 90))]),
            created_at=created_at,
            updated_at=created_at + timedelta(days=random.randint(0, 30))
        )
        db.add(project)
        projects.append(project)
    
    await db.flush()
    print(f"   ✅ Создано {len(projects)} проектов")
    return projects


async def seed_project_skills(db: AsyncSession, projects: List[Project], skills: List[Skill]):
    """Назначение требуемых навыков проектам"""
    print("🔧 Назначение навыков проектам...")
    count = 0
    importance_levels = list(SkillImportance)
    
    for project in projects:
        num = random.randint(2, 8)
        selected_skills = random.sample(skills, min(num, len(skills)))
        for skill in selected_skills:
            project_skill = ProjectSkill(
                project_id=project.id,
                skill_id=skill.id,
                importance=random.choice(importance_levels)
            )
            db.add(project_skill)
            count += 1
    
    await db.flush()
    print(f"   ✅ Назначено {count} требований к навыкам")


async def seed_teams(db: AsyncSession, projects: List[Project], users: List[User]) -> List[Team]:
    """Создание команд"""
    print("👥 Создание команд...")
    teams = []
    regular_users = [u for u in users if u.role == UserRole.USER]
    
    for project in projects:
        num_teams = random.randint(1, 3)
        for i in range(num_teams):
            team = Team(
                project_id=project.id,
                created_by=random.choice(regular_users).id,
                name=f"{fake.word().capitalize()} Team",
                description=fake.sentence() if random.random() > 0.5 else None,
            )
            db.add(team)
            teams.append(team)
    
    await db.flush()
    print(f"   ✅ Создано {len(teams)} команд")
    return teams


async def seed_team_members(db: AsyncSession, teams: List[Team], users: List[User]):
    """Назначение участников в команды"""
    print("🤝 Назначение участников в команды...")
    count = 0
    roles = [TeamRole.MEMBER, TeamRole.MEMBER, TeamRole.MEMBER, TeamRole.OBSERVER, TeamRole.LEAD]
    statuses = [MemberStatus.ACTIVE, MemberStatus.ACTIVE, MemberStatus.ACTIVE, MemberStatus.INVITED]
    regular_users = [u for u in users if u.role == UserRole.USER]
    
    for team in teams:
        num_members = random.randint(2, 8)
        selected_users = random.sample(regular_users, min(num_members, len(regular_users)))
        for user in selected_users:
            team_member = TeamMember(
                team_id=team.id,
                user_id=user.id,
                role_in_team=random.choice(roles),
                status=random.choice(statuses),
            )
            db.add(team_member)
            count += 1
    
    await db.flush()
    print(f"   ✅ Назначено {count} участников в команды")


async def seed_tasks(db: AsyncSession, projects: List[Project], users: List[User]):
    """Создание задач"""
    print("✅ Создание задач...")
    count = 0
    statuses = list(TaskStatus)
    priorities = list(TaskPriority)
    regular_users = [u for u in users if u.role == UserRole.USER]
    
    for project in projects:
        num_tasks = random.randint(3, 15)
        for i in range(num_tasks):
            assignee = random.choice(regular_users) if random.random() > 0.3 else None
            created_at = project.created_at + timedelta(days=random.randint(0, 30))
            
            task = Task(
                project_id=project.id,
                assignee_id=assignee.id if assignee else None,
                title=fake.sentence(nb_words=6),
                description=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
                status=random.choice(statuses),
                priority=random.choice(priorities),
                due_date=datetime.now().date() + timedelta(days=random.randint(1, 90)) if random.random() > 0.5 else None,
                created_at=created_at,
                updated_at=created_at + timedelta(days=random.randint(0, 14))
            )
            db.add(task)
            count += 1
    
    await db.flush()
    print(f"   ✅ Создано {count} задач")


async def main():
    """Основная функция заполнения БД"""
    print("\n" + "="*60)
    print("🌱 НАЧАЛО ЗАПОЛНЕНИЯ БАЗЫ ДАННЫХ ТЕСТОВЫМИ ДАННЫМИ")
    print("="*60 + "\n")
    
    async with AsyncSessionLocal() as db:
        # Очищаем БД
        await clear_database(db)
        
        # Создаем данные
        skills = await seed_skills(db)
        users = await seed_users(db, count=40)
        await seed_user_skills(db, users, skills)
        
        projects = await seed_projects(db, users, count=35)
        await seed_project_skills(db, projects, skills)
        
        teams = await seed_teams(db, projects, users)
        await seed_team_members(db, teams, users)
        
        await seed_tasks(db, projects, users)
        
        # Фиксируем все изменения
        await db.commit()
    
    print("\n" + "="*60)
    print("✅ БАЗА ДАННЫХ УСПЕШНО ЗАПОЛНЕНА!")
    print("="*60)
    print("\n📊 Создано:")
    print(f"   • Навыков: {len(SKILLS_DATA)}")
    print(f"   • Пользователей: ~41 (1 админ + 40 обычных)")
    print(f"   • Проектов: ~35")
    print(f"   • Команд: ~60-80")
    print(f"   • Задач: ~200-300")
    print("\n🔑 Тестовые учетные данные:")
    print("   • Админ:   admin@example.com / admin123")
    print("   • Пользователь: любой email из списка выше / password123")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())