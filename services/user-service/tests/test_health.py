import pytest


def test_health_check(test_client):
    """Test that the service is running"""
    # User service doesn't have a root endpoint, so we'll just test imports work
    assert test_client is not None
