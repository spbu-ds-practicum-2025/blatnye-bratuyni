import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def test_client():
    """Create a test client"""
    with TestClient(app) as client:
        yield client
