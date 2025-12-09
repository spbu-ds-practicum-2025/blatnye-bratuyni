from fastapi import FastAPI
from models import Base
from config import engine
from routes import router
import os

# Создание таблиц только если не в тестовом режиме
if os.getenv("TESTING") != "true":
    Base.metadata.create_all(bind=engine)

app = FastAPI(title="User Service")
app.include_router(router)