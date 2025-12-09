from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    confirmed = Column(Boolean, default=False)
    confirmation_code = Column(String, nullable=True)
    recovery_code = Column(String, nullable=True)
    role = Column(String, default="user", nullable=False)  # "user" or "admin"
    created_at = Column(DateTime, default=datetime.utcnow)
