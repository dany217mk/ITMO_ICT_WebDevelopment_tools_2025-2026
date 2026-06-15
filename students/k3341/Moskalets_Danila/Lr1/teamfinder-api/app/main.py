from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.api.v1 import router as v1_router
from app.core.database import engine
from app.core.exceptions import (
    AppException, 
    UnauthorizedException, 
    ForbiddenException,
    NotFoundException,
    ConflictException
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    yield
    await engine.dispose()


# Создаем приложение FastAPI
app = FastAPI(
    title=settings.APP_NAME,
    description="Платформа для поиска людей в команду для совместной работы над проектами",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== Глобальные обработчики исключений ==========

@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Обработчик 401 Unauthorized"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    """Обработчик 403 Forbidden"""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Обработчик 404 Not Found"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    """Обработчик 409 Conflict"""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """Обработчик базового исключения приложения"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Обработчик ошибок валидации Pydantic (422)"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": 422,
                "message": "Validation error",
                "details": [
                    {
                        "loc": list(e["loc"]),
                        "msg": e["msg"],
                        "type": e["type"]
                    }
                    for e in exc.errors()
                ]
            }
        }
    )


# ========== Подключаем роутеры ==========
app.include_router(v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "docs": "/docs" if settings.DEBUG else None,
        "version": "1.0.0"
    }