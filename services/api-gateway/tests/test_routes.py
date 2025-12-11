import pytest
import jwt
from unittest.mock import patch, MagicMock
from config import SECRET_KEY


@patch('routes.user.requests.post')
def test_register_route(mock_post, test_client):
    """Test user registration through gateway"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"message": "User created"}'
    mock_response.headers = {'content-type': 'application/json'}
    mock_post.return_value = mock_response
    
    response = test_client.post(
        "/users/register",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    mock_post.assert_called_once()


@patch('routes.user.requests.post')
def test_login_route(mock_post, test_client):
    """Test user login through gateway"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"access_token": "fake_token", "token_type": "bearer"}'
    mock_response.headers = {'content-type': 'application/json'}
    mock_post.return_value = mock_response
    
    response = test_client.post(
        "/users/login",
        json={
            "email": "test@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200


@patch('routes.booking.requests.get')
def test_get_zones_route(mock_get, test_client):
    """Test getting zones through gateway"""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'[{"id": 1, "name": "Zone 1"}]'
    mock_response.headers = {'content-type': 'application/json'}
    mock_get.return_value = mock_response
    
    response = test_client.get("/bookings/zones")
    
    assert response.status_code == 200
    mock_get.assert_called_once()


@patch('routes.booking.requests.post')
def test_extend_booking_forwards_body(mock_post, test_client):
    """
    // Тест проверяет, что API Gateway корректно передаёт тело запроса
    // с параметрами extend_hours и extend_minutes в booking service
    """
    # // Мокируем ответ от booking service
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"id": 1, "status": "active"}'
    mock_response.headers = {'content-type': 'application/json'}
    mock_post.return_value = mock_response
    
    # // Создаём валидный JWT токен для аутентификации
    token = jwt.encode({'user_id': 1, 'sub': 1, 'role': 'user'}, SECRET_KEY, algorithm='HS256')
    
    # // Отправляем запрос на продление с телом и токеном
    response = test_client.post(
        "/bookings/1/extend",
        json={
            "extend_hours": 2,
            "extend_minutes": 30
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # // Проверяем успешность запроса
    assert response.status_code == 200
    
    # // Проверяем, что requests.post был вызван с правильными параметрами
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    
    # // Проверяем, что тело запроса передано в booking service
    assert call_args.kwargs['json'] == {"extend_hours": 2, "extend_minutes": 30}
    
    # // Проверяем, что заголовки с user_id переданы
    assert 'headers' in call_args.kwargs
    assert call_args.kwargs['headers']['X-User-Id'] == '1'
