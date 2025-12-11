from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import user, booking, notification, admin

app = FastAPI(
    title="API Gateway",
    description="Единая точка входа для blatnye-bratuyni",
    version="1.0.0"
)

# --------------------------- CORS middleware setup ---------------------------
# // CORS настройки с максимальной доступностью для стабильной работы всех клиентов
# // ВАЖНО: allow_origins=["*"] используется по требованию для максимальной совместимости
# // В продакшене можно ограничить конкретными доменами через переменные окружения
# // allow_origins: ["*"] - разрешаем запросы с любых доменов
# // allow_methods: ["*"] - разрешаем все HTTP методы (GET, POST, PUT, DELETE и т.д.)
# // allow_headers: ["*"] - разрешаем все заголовки запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # // Разрешаем запросы со всех источников
    allow_credentials=True,
    allow_methods=["*"],  # // Разрешаем все HTTP методы
    allow_headers=["*"],  # // Разрешаем все заголовки
)
# ------------------------------------------------------------------------------

# Подключаем роуты, проксирующие бизнес-логику дальше
app.include_router(user.router, prefix="/users", tags=["users"])
app.include_router(booking.router, prefix="/bookings", tags=["bookings"])
app.include_router(notification.router, prefix="/notifications", tags=["notifications"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

@app.get("/")
async def root():
    return {"status": "ok", "gateway": True}