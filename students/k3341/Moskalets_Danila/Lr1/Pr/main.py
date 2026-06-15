from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import select
from contextlib import asynccontextmanager

from models import (
    Warrior, WarriorDefault, WarriorWithProfession,
    WarriorWithSkills, WarriorFull,
    Profession, ProfessionDefault,
    Skill, SkillDefault,
    RaceType
)
from connection import init_db, get_session


# Асинхронный контекстный менеджер для запуска (новый способ вместо on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: создаем таблицы
    init_db()
    print("База данных инициализирована")
    yield
    # Shutdown: здесь можно закрыть соединения
    print("Выключение приложения")


app = FastAPI(
    title="Warriors API",
    description="API для управления воинами с PostgreSQL",
    version="2.0.0",
    lifespan=lifespan
)


# ============= API для воинов =============

@app.get("/")
def hello():
    return {"message": "Hello, Warrior! Добро пожаловать в Warriors API"}


# GET: список всех воинов (без вложенных объектов)
@app.get("/warriors_list", response_model=List[WarriorDefault])
def warriors_list(session=Depends(get_session)):
    """Получить список всех воинов (базовая информация)"""
    warriors = session.exec(select(Warrior)).all()
    return warriors


# GET: воин с профессией
@app.get("/warrior/{warrior_id}", response_model=WarriorWithProfession)
def warrior_get_with_profession(warrior_id: int, session=Depends(get_session)):
    """Получить воина по ID с вложенной профессией"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    return warrior


# GET: воин с умениями
@app.get("/warrior/{warrior_id}/skills", response_model=WarriorWithSkills)
def warrior_get_with_skills(warrior_id: int, session=Depends(get_session)):
    """Получить воина по ID с его умениями"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    return warrior


# GET: полная информация о воине
@app.get("/warrior/{warrior_id}/full", response_model=WarriorFull)
def warrior_get_full(warrior_id: int, session=Depends(get_session)):
    """Получить воина по ID со всеми связями (профессия + умения)"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    return warrior


# POST: создание воина
@app.post("/warrior")
def warrior_create(warrior: WarriorDefault, session=Depends(get_session)):
    """Создать нового воина"""
    db_warrior = Warrior.model_validate(warrior)
    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return {"status": 200, "data": db_warrior}


# PATCH: частичное обновление воина
@app.patch("/warrior/{warrior_id}")
def warrior_update(warrior_id: int, warrior: WarriorDefault, session=Depends(get_session)):
    """Обновить данные воина (частичное обновление)"""
    db_warrior = session.get(Warrior, warrior_id)
    if not db_warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")

    # Обновляем только переданные поля
    warrior_data = warrior.model_dump(exclude_unset=True)
    for key, value in warrior_data.items():
        setattr(db_warrior, key, value)

    session.add(db_warrior)
    session.commit()
    session.refresh(db_warrior)
    return db_warrior


# DELETE: удаление воина
@app.delete("/warrior/{warrior_id}")
def warrior_delete(warrior_id: int, session=Depends(get_session)):
    """Удалить воина по ID"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    session.delete(warrior)
    session.commit()
    return {"status": 200, "message": "Warrior deleted successfully"}


# ============= API для профессий =============

@app.get("/professions_list", response_model=List[Profession])
def professions_list(session=Depends(get_session)):
    """Получить список всех профессий"""
    return session.exec(select(Profession)).all()


@app.get("/profession/{profession_id}", response_model=Profession)
def profession_get(profession_id: int, session=Depends(get_session)):
    """Получить профессию по ID"""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(status_code=404, detail="Profession not found")
    return profession


@app.post("/profession")
def profession_create(prof: ProfessionDefault, session=Depends(get_session)):
    """Создать новую профессию"""
    db_prof = Profession.model_validate(prof)
    session.add(db_prof)
    session.commit()
    session.refresh(db_prof)
    return {"status": 200, "data": db_prof}


@app.patch("/profession/{profession_id}")
def profession_update(profession_id: int, prof: ProfessionDefault, session=Depends(get_session)):
    """Обновить профессию"""
    db_prof = session.get(Profession, profession_id)
    if not db_prof:
        raise HTTPException(status_code=404, detail="Profession not found")

    prof_data = prof.model_dump(exclude_unset=True)
    for key, value in prof_data.items():
        setattr(db_prof, key, value)

    session.add(db_prof)
    session.commit()
    session.refresh(db_prof)
    return db_prof


@app.delete("/profession/{profession_id}")
def profession_delete(profession_id: int, session=Depends(get_session)):
    """Удалить профессию"""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(status_code=404, detail="Profession not found")
    session.delete(profession)
    session.commit()
    return {"status": 200, "message": "Profession deleted successfully"}


# ============= API для умений =============

@app.get("/skills_list", response_model=List[Skill])
def skills_list(session=Depends(get_session)):
    """Получить список всех умений"""
    return session.exec(select(Skill)).all()


@app.get("/skill/{skill_id}", response_model=Skill)
def skill_get(skill_id: int, session=Depends(get_session)):
    """Получить умение по ID"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@app.post("/skill")
def skill_create(skill: SkillDefault, session=Depends(get_session)):
    """Создать новое умение"""
    db_skill = Skill.model_validate(skill)
    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return {"status": 200, "data": db_skill}


@app.patch("/skill/{skill_id}")
def skill_update(skill_id: int, skill: SkillDefault, session=Depends(get_session)):
    """Обновить умение"""
    db_skill = session.get(Skill, skill_id)
    if not db_skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    skill_data = skill.model_dump(exclude_unset=True)
    for key, value in skill_data.items():
        setattr(db_skill, key, value)

    session.add(db_skill)
    session.commit()
    session.refresh(db_skill)
    return db_skill


@app.delete("/skill/{skill_id}")
def skill_delete(skill_id: int, session=Depends(get_session)):
    """Удалить умение"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    session.delete(skill)
    session.commit()
    return {"status": 200, "message": "Skill deleted successfully"}


# ============= API для связей (добавление умений воину) =============

@app.post("/warrior/{warrior_id}/add-skill/{skill_id}")
def add_skill_to_warrior(warrior_id: int, skill_id: int, session=Depends(get_session)):
    """Добавить умение воину (связь many-to-many)"""
    warrior = session.get(Warrior, warrior_id)
    skill = session.get(Skill, skill_id)

    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    # Добавляем умение воину
    if skill not in warrior.skills:
        warrior.skills.append(skill)
        session.commit()
        session.refresh(warrior)
        return {"status": 200, "message": f"Skill '{skill.name}' added to warrior '{warrior.name}'"}
    else:
        return {"status": 400, "message": "Warrior already has this skill"}


@app.delete("/warrior/{warrior_id}/remove-skill/{skill_id}")
def remove_skill_from_warrior(warrior_id: int, skill_id: int, session=Depends(get_session)):
    """Удалить умение у воина"""
    warrior = session.get(Warrior, warrior_id)
    skill = session.get(Skill, skill_id)

    if not warrior:
        raise HTTPException(status_code=404, detail="Warrior not found")
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")

    if skill in warrior.skills:
        warrior.skills.remove(skill)
        session.commit()
        return {"status": 200, "message": f"Skill '{skill.name}' removed from warrior '{warrior.name}'"}
    else:
        return {"status": 400, "message": "Warrior does not have this skill"}