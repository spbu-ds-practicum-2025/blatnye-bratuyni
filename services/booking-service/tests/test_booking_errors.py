import pytest
from datetime import date, timedelta

import models


@pytest.mark.asyncio
async def test_invalid_date_error(test_client, test_session):
    """Тест проверки ошибки при некорректной дате"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": "invalid-date",
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 409
    json_data = response.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "INVALID_DATE"


@pytest.mark.asyncio
async def test_invalid_time_range_error(test_client, test_session):
    """Тест проверки ошибки при некорректном временном интервале (конец раньше начала)"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 12,
            "start_minute": 0,
            "end_hour": 10,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 409
    json_data = response.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "INVALID_TIME_RANGE"


@pytest.mark.asyncio
async def test_time_limit_exceeded_error(test_client, test_session):
    """Тест проверки ошибки при превышении лимита времени бронирования"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    # Пытаемся забронировать на 7 часов (лимит 6)
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 9,
            "start_minute": 0,
            "end_hour": 16,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 409
    json_data = response.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "TIME_LIMIT_EXCEEDED"


@pytest.mark.asyncio
async def test_zone_inactive_error(test_client, test_session):
    """Тест проверки ошибки при попытке бронирования в неактивной зоне"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=False)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 409
    json_data = response.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "ZONE_INACTIVE"


@pytest.mark.asyncio
async def test_user_conflict_error(test_client, test_session):
    """Тест проверки ошибки при конфликте бронирований пользователя"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    # Создаём первую бронь
    response1 = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response1.status_code == 201
    
    # Пытаемся создать вторую бронь тем же пользователем на пересекающееся время
    response2 = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 11,
            "start_minute": 0,
            "end_hour": 13,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response2.status_code == 409
    json_data = response2.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "USER_CONFLICT"


@pytest.mark.asyncio
async def test_zone_capacity_exceeded_error(test_client, test_session):
    """Тест проверки ошибки при переполнении зоны"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    # Создаём первую бронь
    response1 = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response1.status_code == 201
    
    # Пытаемся создать вторую бронь другим пользователем на то же время
    response2 = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "2", "X-User-Role": "user"}
    )
    assert response2.status_code == 409
    json_data = response2.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "ZONE_CAPACITY_EXCEEDED"


@pytest.mark.asyncio
async def test_zone_without_places_capacity_error(test_client, test_session):
    """Тест проверки ошибки при попытке бронирования в зоне без мест"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.commit()
    
    target_date = date.today()
    # Попытка создать бронь в зоне без мест возвращает ZONE_CAPACITY_EXCEEDED (max_capacity = 0)
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 409
    json_data = response.json()
    assert "code" in json_data["detail"]
    assert json_data["detail"]["code"] == "ZONE_CAPACITY_EXCEEDED"


@pytest.mark.asyncio
async def test_successful_booking_still_works(test_client, test_session):
    """Тест проверки, что успешное создание брони все еще работает"""
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.commit()
    
    target_date = date.today()
    response = await test_client.post(
        "/bookings/by-time",
        json={
            "zone_id": zone.id,
            "date": target_date.isoformat(),
            "start_hour": 10,
            "start_minute": 0,
            "end_hour": 12,
            "end_minute": 0,
        },
        headers={"X-User-Id": "1", "X-User-Role": "user"}
    )
    assert response.status_code == 201
    json_data = response.json()
    assert "id" in json_data
    assert json_data["user_id"] == 1
    assert json_data["status"] == "active"
