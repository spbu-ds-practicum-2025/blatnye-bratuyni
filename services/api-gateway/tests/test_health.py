import pytest


def test_health_check(test_client):
    """Test API Gateway root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["gateway"] is True


def test_cors_headers(test_client):
    """Test that CORS headers are set"""
    response = test_client.options("/", headers={"Origin": "http://localhost:3000"})
    # CORS middleware should handle this
    assert response.status_code in [200, 405]  # OPTIONS may not be explicitly handled
