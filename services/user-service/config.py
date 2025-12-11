import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Параметры DB
DB_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@user-db:5432/userservice")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SMTP
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "1025"))
SMTP_USER = os.getenv("SMTP_USER", "user")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "password")

# JWT
SECRET_KEY = os.getenv("JWT_SECRET", "a-string-secret-at-least-256-bits-long")
ACCESS_TOKEN_EXPIRE_MINUTES = 60