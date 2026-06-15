# main.py
import os
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from sqlmodel import select
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from models import (
    Warrior, WarriorDefault, WarriorWithProfession,
    WarriorWithSkills, WarriorFull,
    Profession, ProfessionDefault,
    Skill, SkillDefault,
    RaceType
)
from connection import init_db, get_session

# Получаем настройки из .env
APP_NAME = os.getenv('APP_NAME', 'Warriors API')
APP_VERSION = os.getenv('APP_VERSION', '1.0.0')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
HOST = os.getenv('HOST', '127.0.0.1')
PORT = int(os.getenv('PORT', '8000'))


# Асинхронный контекстный менеджер для запуска
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup: создаем таблицы
    init_db()
    print(f"{APP_NAME} v{APP_VERSION} инициализирован")
    print(f"Режим отладки: {'Включен' if DEBUG else 'Выключен'}")
    print(f"Сервер запущен на http://{HOST}:{PORT}")
    yield
    # Shutdown
    print("Завершение работы приложения...")


app = FastAPI(
    title=APP_NAME,
    description="API для управления воинами с PostgreSQL.\n\n"
                "## Возможности:\n"
                "- CRUD операции с воинами\n"
                "- Управление профессиями\n"
                "- Управление умениями\n"
                "- Связи many-to-many между воинами и умениями\n"
                "- Автоматическая документация Swagger",
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ============= Корневой эндпоинт =============

@app.get(
    "/",
    summary="Приветственное сообщение",
    description="Возвращает приветствие и основную информацию об API"
)
def hello():
    """Корневой эндпоинт API"""
    return {
        "message": "Hello, Warrior! Добро пожаловать в Warriors API",
        "version": APP_VERSION,
        "docs": "/docs",
        "endpoints": {
            "warriors": "/warriors_list",
            "professions": "/professions_list",
            "skills": "/skills_list"
        }
    }


# ============= API для воинов =============

@app.get(
    "/warriors_list",
    response_model=List[WarriorDefault],
    summary="Получить всех воинов",
    description="Возвращает список всех воинов без вложенных объектов (базовая информация)"
)
def warriors_list(session=Depends(get_session)):
    """Получить список всех воинов"""
    warriors = session.exec(select(Warrior)).all()
    return warriors


@app.get(
    "/warrior/{warrior_id}",
    response_model=WarriorWithProfession,
    summary="Получить воина по ID",
    description="Возвращает информацию о воине с вложенной профессией"
)
def warrior_get_with_profession(
        warrior_id: int,
        session=Depends(get_session)
):
    """Получить воина по ID с профессией"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )
    return warrior


@app.get(
    "/warrior/{warrior_id}/skills",
    response_model=WarriorWithSkills,
    summary="Получить воина с умениями",
    description="Возвращает воина и список его умений"
)
def warrior_get_with_skills(
        warrior_id: int,
        session=Depends(get_session)
):
    """Получить воина по ID с его умениями"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )
    return warrior


@app.get(
    "/warrior/{warrior_id}/full",
    response_model=WarriorFull,
    summary="Полная информация о воине",
    description="Возвращает воина с профессией и всеми умениями"
)
def warrior_get_full(
        warrior_id: int,
        session=Depends(get_session)
):
    """Получить полную информацию о воине (профессия + умения)"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )
    return warrior


@app.post(
    "/warrior",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Создать воина",
    description="Создает нового воина в базе данных"
)
def warrior_create(
        warrior: WarriorDefault,
        session=Depends(get_session)
):
    """Создать нового воина"""
    try:
        db_warrior = Warrior.model_validate(warrior)
        session.add(db_warrior)
        session.commit()
        session.refresh(db_warrior)
        return {
            "status": status.HTTP_200_OK,
            "message": "Воин успешно создан",
            "data": db_warrior
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании воина: {str(e)}"
        )


@app.patch(
    "/warrior/{warrior_id}",
    response_model=WarriorDefault,
    summary="Обновить воина",
    description="Частичное обновление данных воина"
)
def warrior_update(
        warrior_id: int,
        warrior: WarriorDefault,
        session=Depends(get_session)
):
    """Обновить данные воина (частичное обновление)"""
    db_warrior = session.get(Warrior, warrior_id)
    if not db_warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )

    # Обновляем только переданные поля
    warrior_data = warrior.model_dump(exclude_unset=True)
    for key, value in warrior_data.items():
        setattr(db_warrior, key, value)

    try:
        session.add(db_warrior)
        session.commit()
        session.refresh(db_warrior)
        return db_warrior
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении воина: {str(e)}"
        )


@app.delete(
    "/warrior/{warrior_id}",
    status_code=status.HTTP_200_OK,
    summary="Удалить воина",
    description="Удаляет воина из базы данных"
)
def warrior_delete(
        warrior_id: int,
        session=Depends(get_session)
):
    """Удалить воина по ID"""
    warrior = session.get(Warrior, warrior_id)
    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )

    try:
        session.delete(warrior)
        session.commit()
        return {
            "status": status.HTTP_200_OK,
            "message": f"Воин '{warrior.name}' успешно удален"
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении воина: {str(e)}"
        )


# ============= API для профессий =============

@app.get(
    "/professions_list",
    response_model=List[Profession],
    summary="Получить все профессии",
    description="Возвращает список всех профессий"
)
def professions_list(session=Depends(get_session)):
    """Получить список всех профессий"""
    return session.exec(select(Profession)).all()


@app.get(
    "/profession/{profession_id}",
    response_model=Profession,
    summary="Получить профессию по ID",
    description="Возвращает информацию о профессии"
)
def profession_get(
        profession_id: int,
        session=Depends(get_session)
):
    """Получить профессию по ID"""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Профессия с ID {profession_id} не найдена"
        )
    return profession


@app.post(
    "/profession",
    status_code=status.HTTP_201_CREATED,
    summary="Создать профессию",
    description="Создает новую профессию"
)
def profession_create(
        prof: ProfessionDefault,
        session=Depends(get_session)
):
    """Создать новую профессию"""
    try:
        db_prof = Profession.model_validate(prof)
        session.add(db_prof)
        session.commit()
        session.refresh(db_prof)
        return {
            "status": status.HTTP_200_OK,
            "message": "Профессия успешно создана",
            "data": db_prof
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании профессии: {str(e)}"
        )


@app.patch(
    "/profession/{profession_id}",
    response_model=Profession,
    summary="Обновить профессию",
    description="Частичное обновление данных профессии"
)
def profession_update(
        profession_id: int,
        prof: ProfessionDefault,
        session=Depends(get_session)
):
    """Обновить профессию"""
    db_prof = session.get(Profession, profession_id)
    if not db_prof:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Профессия с ID {profession_id} не найдена"
        )

    prof_data = prof.model_dump(exclude_unset=True)
    for key, value in prof_data.items():
        setattr(db_prof, key, value)

    try:
        session.add(db_prof)
        session.commit()
        session.refresh(db_prof)
        return db_prof
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении профессии: {str(e)}"
        )


@app.delete(
    "/profession/{profession_id}",
    summary="Удалить профессию",
    description="Удаляет профессию из базы данных"
)
def profession_delete(
        profession_id: int,
        session=Depends(get_session)
):
    """Удалить профессию"""
    profession = session.get(Profession, profession_id)
    if not profession:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Профессия с ID {profession_id} не найдена"
        )

    try:
        session.delete(profession)
        session.commit()
        return {
            "status": status.HTTP_200_OK,
            "message": f"Профессия '{profession.title}' успешно удалена"
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении профессии: {str(e)}"
        )


# ============= API для умений =============

@app.get(
    "/skills_list",
    response_model=List[Skill],
    summary="Получить все умения",
    description="Возвращает список всех умений"
)
def skills_list(session=Depends(get_session)):
    """Получить список всех умений"""
    return session.exec(select(Skill)).all()


@app.get(
    "/skill/{skill_id}",
    response_model=Skill,
    summary="Получить умение по ID",
    description="Возвращает информацию об умении"
)
def skill_get(
        skill_id: int,
        session=Depends(get_session)
):
    """Получить умение по ID"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Умение с ID {skill_id} не найдено"
        )
    return skill


@app.post(
    "/skill",
    status_code=status.HTTP_201_CREATED,
    summary="Создать умение",
    description="Создает новое умение"
)
def skill_create(
        skill: SkillDefault,
        session=Depends(get_session)
):
    """Создать новое умение"""
    try:
        db_skill = Skill.model_validate(skill)
        session.add(db_skill)
        session.commit()
        session.refresh(db_skill)
        return {
            "status": status.HTTP_200_OK,
            "message": "Умение успешно создано",
            "data": db_skill
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при создании умения: {str(e)}"
        )


@app.patch(
    "/skill/{skill_id}",
    response_model=Skill,
    summary="Обновить умение",
    description="Частичное обновление данных умения"
)
def skill_update(
        skill_id: int,
        skill: SkillDefault,
        session=Depends(get_session)
):
    """Обновить умение"""
    db_skill = session.get(Skill, skill_id)
    if not db_skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Умение с ID {skill_id} не найдено"
        )

    skill_data = skill.model_dump(exclude_unset=True)
    for key, value in skill_data.items():
        setattr(db_skill, key, value)

    try:
        session.add(db_skill)
        session.commit()
        session.refresh(db_skill)
        return db_skill
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при обновлении умения: {str(e)}"
        )


@app.delete(
    "/skill/{skill_id}",
    summary="Удалить умение",
    description="Удаляет умение из базы данных"
)
def skill_delete(
        skill_id: int,
        session=Depends(get_session)
):
    """Удалить умение"""
    skill = session.get(Skill, skill_id)
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Умение с ID {skill_id} не найдено"
        )

    try:
        session.delete(skill)
        session.commit()
        return {
            "status": status.HTTP_200_OK,
            "message": f"Умение '{skill.name}' успешно удалено"
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при удалении умения: {str(e)}"
        )


# ============= API для связей (many-to-many) =============

@app.post(
    "/warrior/{warrior_id}/add-skill/{skill_id}",
    summary="Добавить умение воину",
    description="Создает связь many-to-many между воином и умением"
)
def add_skill_to_warrior(
        warrior_id: int,
        skill_id: int,
        session=Depends(get_session)
):
    """Добавить умение воину"""
    warrior = session.get(Warrior, warrior_id)
    skill = session.get(Skill, skill_id)

    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Умение с ID {skill_id} не найдено"
        )

    # Добавляем умение воину
    if skill not in warrior.skills:
        warrior.skills.append(skill)
        session.commit()
        session.refresh(warrior)
        return {
            "status": status.HTTP_200_OK,
            "message": f"Умение '{skill.name}' добавлено воину '{warrior.name}'"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У воина уже есть это умение"
        )


@app.delete(
    "/warrior/{warrior_id}/remove-skill/{skill_id}",
    summary="Удалить умение у воина",
    description="Удаляет связь many-to-many между воином и умением"
)
def remove_skill_from_warrior(
        warrior_id: int,
        skill_id: int,
        session=Depends(get_session)
):
    """Удалить умение у воина"""
    warrior = session.get(Warrior, warrior_id)
    skill = session.get(Skill, skill_id)

    if not warrior:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Воин с ID {warrior_id} не найден"
        )
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Умение с ID {skill_id} не найдено"
        )

    if skill in warrior.skills:
        warrior.skills.remove(skill)
        session.commit()
        return {
            "status": status.HTTP_200_OK,
            "message": f"Умение '{skill.name}' удалено у воина '{warrior.name}'"
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="У воина нет этого умения"
        )


# ============= Дополнительный эндпоинт для статистики =============

@app.get(
    "/stats",
    summary="Статистика базы данных",
    description="Возвращает статистику по количеству записей"
)
def get_stats(session=Depends(get_session)):
    """Получить статистику БД"""
    warriors_count = session.exec(select(Warrior)).all().count
    professions_count = session.exec(select(Profession)).all().count
    skills_count = session.exec(select(Skill)).all().count

    return {
        "total_warriors": len(warriors_count) if warriors_count else 0,
        "total_professions": len(professions_count) if professions_count else 0,
        "total_skills": len(skills_count) if skills_count else 0
    }


# Если запускаем файл напрямую
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=DEBUG
    )