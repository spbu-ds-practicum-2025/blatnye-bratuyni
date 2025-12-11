# services/booking-service/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes import router as user_router
from admin import router as admin_router

from db import engine
from models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ----------------------------
    # ВРЕМЕННОЕ РЕШЕНИЕ:
    # создаём таблицы при старте сервиса.
    # Потом это будет заменено Alembic миграциями.
    # ----------------------------
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield  # ← запуск приложения


app = FastAPI(
    title="Booking Service",
    lifespan=lifespan,
)

# // CORS middleware для поддержки прямых запросов к сервису (без API Gateway)
# // Обеспечиваем максимальную доступность для стабильной работы в любом workflow
# // ВАЖНО: allow_origins=["*"] используется по требованию для максимальной совместимости
# // В продакшене можно ограничить конкретными доменами через переменные окружения
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # // Разрешаем запросы со всех источников
    allow_credentials=True,
    allow_methods=["*"],  # // Разрешаем все HTTP методы
    allow_headers=["*"],  # // Разрешаем все заголовки
)


@app.get("/", tags=["service"])
async def root():
    return {"message": "Booking Service is running"}


app.include_router(user_router)
app.include_router(admin_router)
