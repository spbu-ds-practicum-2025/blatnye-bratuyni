import pytest


@pytest.mark.asyncio
async def test_health_check(test_client):
    """Test health check endpoint"""
    response = await test_client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Booking Service is running"
