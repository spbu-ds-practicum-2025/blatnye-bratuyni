import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Set testing mode before importing main
os.environ["TESTING"] = "true"

from main import app
from models import Base


# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///./test_notifications.db"


@pytest.fixture(scope="function")
def test_db():
    """Create a test database"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()
    
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client():
    """Create a test client"""
    with TestClient(app) as client:
        yield client
