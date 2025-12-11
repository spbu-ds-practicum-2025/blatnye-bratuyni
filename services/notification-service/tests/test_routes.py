import pytest
from unittest.mock import patch, MagicMock


def test_send_email_endpoint_success(test_client):
    """Test successful email sending"""
    with patch('routes.send_email') as mock_send:
        mock_send.return_value = True
        
        response = test_client.post(
            "/notify/email",
            json={
                "email": "test@example.com",
                "subject": "Test Subject",
                "text": "Test message"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        mock_send.assert_called_once()


def test_send_email_endpoint_failure(test_client):
    """Test failed email sending"""
    with patch('routes.send_email') as mock_send:
        mock_send.return_value = False
        
        response = test_client.post(
            "/notify/email",
            json={
                "email": "test@example.com",
                "subject": "Test Subject",
                "text": "Test message"
            }
        )
        
        assert response.status_code == 500


def test_send_email_invalid_email(test_client):
    """Test sending email with invalid email address"""
    response = test_client.post(
        "/notify/email",
        json={
            "email": "invalid-email",
            "subject": "Test Subject",
            "text": "Test message"
        }
    )
    
    # Should fail validation
    assert response.status_code == 422
