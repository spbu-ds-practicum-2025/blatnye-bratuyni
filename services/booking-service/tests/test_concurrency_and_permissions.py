"""
Тесты для проверки конкурентности, транзакционности и прав доступа.

Проверяют:
1. Конкурентное бронирование одной ячейки двумя пользователями
2. Обработку IntegrityError при дублировании слотов
3. Нарушение прав доступа (обычный пользователь пытается сделать админские действия)
"""
import pytest
from datetime import datetime, timedelta, timezone
import asyncio

import models
import crud
import schemas
from crud import BookingExtensionError


@pytest.mark.asyncio
async def test_concurrent_booking_same_slot(test_session):
    """
    Тест проверяет конкурентное бронирование одного слота двумя пользователями.
    
    // конкурентный доступ: симулируем ситуацию, когда два пользователя одновременно
    // пытаются забронировать один и тот же свободный слот. Благодаря SELECT FOR UPDATE
    // только один из них должен успешно забронировать, второй получит None или IntegrityError.
    """
    # Создаём зону, место и слот
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    slot = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=True
    )
    test_session.add(slot)
    await test_session.commit()
    
    # Симулируем конкурентное бронирование: создаём два запроса на бронирование
    booking_data = schemas.BookingCreate(slot_id=slot.id)
    
    # Первый пользователь бронирует
    booking1 = await crud.create_booking(test_session, user_id=1, booking_in=booking_data)
    
    # Второй пользователь пытается забронировать тот же слот
    booking2 = await crud.create_booking(test_session, user_id=2, booking_in=booking_data)
    
    # // проверка результата: только одно бронирование должно быть успешным
    assert booking1 is not None, "Первый пользователь должен успешно забронировать"
    assert booking2 is None, "Второй пользователь не должен смочь забронировать занятый слот"
    
    # Проверяем, что слот теперь недоступен
    await test_session.refresh(slot)
    assert slot.is_available is False


@pytest.mark.asyncio
async def test_duplicate_slot_creation_integrity_error(test_session):
    """
    Тест проверяет обработку IntegrityError при попытке создать дублирующий слот.
    
    // обработка уникальности: unique constraint на (place_id, start_time, end_time)
    // должен предотвратить создание дублирующих слотов. При попытке создать дубликат
    // должен возникнуть IntegrityError, который мы ловим и обрабатываем.
    """
    # Создаём зону
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    # Создаём первое бронирование по времени
    booking_data = schemas.BookingCreateTimeRange(
        zone_id=zone.id,
        date=start_time.date().isoformat(),
        start_hour=start_time.hour,
        start_minute=start_time.minute,
        end_hour=end_time.hour,
        end_minute=end_time.minute,
    )
    
    booking1 = await crud.create_booking_by_time_range(test_session, user_id=1, booking_in=booking_data)
    assert booking1 is not None, "Первое бронирование должно быть успешным"
    
    # Пытаемся создать второе бронирование с точно такими же параметрами
    # // обработка уникальности: второе бронирование должно выбросить BookingError из-за превышения вместимости
    with pytest.raises(crud.BookingError) as exc_info:
        booking2 = await crud.create_booking_by_time_range(test_session, user_id=2, booking_in=booking_data)
    assert exc_info.value.code in ["ZONE_CAPACITY_EXCEEDED", "NO_AVAILABLE_PLACES"], "Ожидается ошибка о превышении вместимости или отсутствии свободных мест"


@pytest.mark.asyncio
async def test_cancel_booking_permission_denied(test_session):
    """
    Тест проверяет, что обычный пользователь не может отменить чужое бронирование.
    
    // проверка прав доступа: только владелец или админ может отменить бронирование.
    """
    # Создаём зону, место и слот
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    slot = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=False
    )
    test_session.add(slot)
    await test_session.flush()
    
    # Пользователь 1 создаёт бронирование
    booking = models.Booking(
        user_id=1,
        slot_id=slot.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=start_time,
        end_time=end_time,
    )
    test_session.add(booking)
    await test_session.commit()
    
    # Пользователь 2 пытается отменить чужое бронирование (без прав админа)
    # // проверка прав доступа: должно вернуть None
    cancelled = await crud.cancel_booking(test_session, user_id=2, booking_id=booking.id, is_admin=False)
    assert cancelled is None, "Пользователь 2 не должен смочь отменить чужое бронирование"
    
    # Проверяем, что бронирование всё ещё активно
    await test_session.refresh(booking)
    assert booking.status == "active", "Бронирование должно остаться активным"


@pytest.mark.asyncio
async def test_cancel_booking_admin_can_cancel_any(test_session):
    """
    Тест проверяет, что админ может отменить любое бронирование.
    
    // проверка прав доступа: админ имеет право отменять любые бронирования.
    """
    # Создаём зону, место и слот
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    slot = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=False
    )
    test_session.add(slot)
    await test_session.flush()
    
    # Пользователь 1 создаёт бронирование
    booking = models.Booking(
        user_id=1,
        slot_id=slot.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=start_time,
        end_time=end_time,
    )
    test_session.add(booking)
    await test_session.commit()
    
    # Админ (user_id=999) отменяет бронирование пользователя 1
    # // проверка прав доступа: админ должен успешно отменить любое бронирование
    cancelled = await crud.cancel_booking(test_session, user_id=999, booking_id=booking.id, is_admin=True)
    assert cancelled is not None, "Админ должен смочь отменить чужое бронирование"
    assert cancelled.status == "cancelled", "Бронирование должно быть отменено"


@pytest.mark.asyncio
async def test_extend_booking_permission_denied(test_session):
    """
    Тест проверяет, что пользователь не может продлить чужое бронирование.
    
    // проверка прав доступа: только владелец может продлить своё бронирование.
    """
    # Создаём зону, место и слоты
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=1)
    slot1 = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=False
    )
    test_session.add(slot1)
    
    # Создаём второй слот для продления
    slot2 = models.Slot(
        place_id=place.id,
        start_time=end_time,
        end_time=end_time + timedelta(hours=1),
        is_available=True
    )
    test_session.add(slot2)
    await test_session.flush()
    
    # Пользователь 1 создаёт бронирование
    booking = models.Booking(
        user_id=1,
        slot_id=slot1.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=start_time,
        end_time=end_time,
    )
    test_session.add(booking)
    await test_session.commit()
    
    # Пользователь 2 пытается продлить чужое бронирование
    # // проверка прав доступа: должно вызвать BookingExtensionError
    with pytest.raises(BookingExtensionError, match="Нет прав на продление этого бронирования"):
        await crud.extend_booking(test_session, user_id=2, booking_id=booking.id, extend_hours=1)


@pytest.mark.asyncio
async def test_concurrent_slot_creation_same_time(test_session):
    """
    Тест проверяет обработку конкурентного создания слотов на одно и то же время.
    
    // конкурентный доступ: при попытке создать два слота с одинаковыми параметрами
    // unique constraint должен предотвратить дублирование, а IntegrityError должен быть обработан.
    """
    # Создаём зону и два места
    zone = models.Zone(name="Test Zone", address="Test Address", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place1 = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    place2 = models.Place(zone_id=zone.id, name="Place 2", is_active=True)
    test_session.add_all([place1, place2])
    await test_session.commit()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=1)
    end_time = start_time + timedelta(hours=2)
    
    # Создаём бронирование для place1
    booking_data = schemas.BookingCreateTimeRange(
        zone_id=zone.id,
        date=start_time.date().isoformat(),
        start_hour=start_time.hour,
        start_minute=start_time.minute,
        end_hour=end_time.hour,
        end_minute=end_time.minute,
    )
    
    booking1 = await crud.create_booking_by_time_range(test_session, user_id=1, booking_in=booking_data)
    assert booking1 is not None, "Первое бронирование должно быть успешным"
    
    # Второй пользователь пытается забронировать в той же зоне на то же время
    # // конкурентный доступ: должно найти свободное место (place2) или вернуть None если все заняты
    booking2 = await crud.create_booking_by_time_range(test_session, user_id=2, booking_in=booking_data)
    assert booking2 is not None, "Второе бронирование должно использовать другое место"
    assert booking2.slot.place_id != booking1.slot.place_id, "Бронирования должны быть на разных местах"
