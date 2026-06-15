from fastapi import APIRouter

from app.api.v1 import health, auth, users, skills, projects, teams, tasks, admin, parser  

router = APIRouter()
router.include_router(health.router)
router.include_router(auth.router)
router.include_router(users.router)
router.include_router(skills.router)
router.include_router(projects.router)
router.include_router(teams.router)
router.include_router(tasks.router)
router.include_router(admin.router)
router.include_router(parser.router)