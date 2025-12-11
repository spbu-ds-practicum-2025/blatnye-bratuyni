import pytest


def test_health_check(test_client):
    """Test that notification service is running"""
    response = test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Notification Service is running"
