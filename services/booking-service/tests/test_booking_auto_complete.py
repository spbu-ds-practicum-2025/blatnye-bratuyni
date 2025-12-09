import pytest
from datetime import datetime, timedelta, timezone

import models
import crud


@pytest.mark.asyncio
async def test_auto_complete_expired_bookings_single(test_session):
    """Тест проверяет автоматическое завершение одного истёкшего бронирования"""
    # Создаём зону и место
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    # Создаём слот который уже истёк
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=3)
    end_time = now - timedelta(hours=1)  # Истёк 1 час назад
    
    slot = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=False
    )
    test_session.add(slot)
    await test_session.flush()
    
    # Создаём активное бронирование которое должно завершиться
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
    
    # Проверяем что бронирование активно
    assert booking.status == "active"
    
    # Вызываем функцию автозавершения
    await crud.auto_complete_expired_bookings(test_session, booking)
    
    # Обновляем объект из БД
    await test_session.refresh(booking)
    
    # Проверяем что статус изменился на completed
    assert booking.status == "completed"


@pytest.mark.asyncio
async def test_auto_complete_expired_bookings_bulk(test_session):
    """Тест проверяет автоматическое завершение всех истёкших бронирований"""
    # Создаём зону и места
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place1 = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    place2 = models.Place(zone_id=zone.id, name="Place 2", is_active=True)
    test_session.add_all([place1, place2])
    await test_session.flush()
    
    now = datetime.now(timezone.utc)
    
    # Создаём истёкший слот для place1
    expired_slot1 = models.Slot(
        place_id=place1.id,
        start_time=now - timedelta(hours=3),
        end_time=now - timedelta(hours=1),
        is_available=False
    )
    test_session.add(expired_slot1)
    await test_session.flush()
    
    # Создаём истёкший слот для place2
    expired_slot2 = models.Slot(
        place_id=place2.id,
        start_time=now - timedelta(hours=2),
        end_time=now - timedelta(minutes=30),
        is_available=False
    )
    test_session.add(expired_slot2)
    await test_session.flush()
    
    # Создаём активный слот (не истёкший)
    active_slot = models.Slot(
        place_id=place1.id,
        start_time=now - timedelta(minutes=30),
        end_time=now + timedelta(hours=1),
        is_available=False
    )
    test_session.add(active_slot)
    await test_session.flush()
    
    # Создаём бронирования
    expired_booking1 = models.Booking(
        user_id=1,
        slot_id=expired_slot1.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=expired_slot1.start_time,
        end_time=expired_slot1.end_time,
    )
    expired_booking2 = models.Booking(
        user_id=2,
        slot_id=expired_slot2.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=expired_slot2.start_time,
        end_time=expired_slot2.end_time,
    )
    active_booking = models.Booking(
        user_id=3,
        slot_id=active_slot.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=active_slot.start_time,
        end_time=active_slot.end_time,
    )
    test_session.add_all([expired_booking1, expired_booking2, active_booking])
    await test_session.commit()
    
    # Вызываем функцию массового автозавершения
    await crud.auto_complete_expired_bookings(test_session)
    
    # Обновляем объекты из БД
    await test_session.refresh(expired_booking1)
    await test_session.refresh(expired_booking2)
    await test_session.refresh(active_booking)
    
    # Проверяем что истёкшие брони завершены
    assert expired_booking1.status == "completed"
    assert expired_booking2.status == "completed"
    # А активная бронь осталась активной
    assert active_booking.status == "active"


@pytest.mark.asyncio
async def test_extend_expired_booking_error(test_session):
    """Тест проверяет что нельзя продлить истёкшее бронирование"""
    # Создаём зону и место
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    # Создаём слот который уже истёк
    now = datetime.now(timezone.utc)
    start_time = now - timedelta(hours=3)
    end_time = now - timedelta(hours=1)
    
    slot = models.Slot(
        place_id=place.id,
        start_time=start_time,
        end_time=end_time,
        is_available=False
    )
    test_session.add(slot)
    await test_session.flush()
    
    # Создаём истёкшее бронирование
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
    
    # Пытаемся продлить истёкшую бронь
    with pytest.raises(crud.BookingExtensionError) as exc_info:
        await crud.extend_booking(
            test_session,
            user_id=1,
            booking_id=booking.id,
            extend_hours=1,
        )
    
    # Проверяем что получили правильную ошибку
    assert exc_info.value.code == "booking_expired"
    assert "истёк" in exc_info.value.message.lower()
    
    # Проверяем что бронирование автоматически завершилось
    await test_session.refresh(booking)
    assert booking.status == "completed"


@pytest.mark.asyncio
async def test_statistics_exclude_completed_bookings(test_session):
    """Тест проверяет что завершённые брони не учитываются в статистике"""
    # Создаём зону и место
    zone = models.Zone(name="Test Zone", address="Test Addr", is_active=True)
    test_session.add(zone)
    await test_session.flush()
    
    place = models.Place(zone_id=zone.id, name="Place 1", is_active=True)
    test_session.add(place)
    await test_session.flush()
    
    now = datetime.now(timezone.utc)
    
    # Создаём активное бронирование (текущее)
    active_slot = models.Slot(
        place_id=place.id,
        start_time=now - timedelta(minutes=30),
        end_time=now + timedelta(hours=1),
        is_available=False
    )
    test_session.add(active_slot)
    await test_session.flush()
    
    active_booking = models.Booking(
        user_id=1,
        slot_id=active_slot.id,
        status="active",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=active_slot.start_time,
        end_time=active_slot.end_time,
    )
    test_session.add(active_booking)
    
    # Создаём завершённое бронирование
    completed_slot = models.Slot(
        place_id=place.id,
        start_time=now - timedelta(hours=3),
        end_time=now - timedelta(hours=1),
        is_available=False
    )
    test_session.add(completed_slot)
    await test_session.flush()
    
    completed_booking = models.Booking(
        user_id=2,
        slot_id=completed_slot.id,
        status="completed",
        zone_name=zone.name,
        zone_address=zone.address,
        start_time=completed_slot.start_time,
        end_time=completed_slot.end_time,
    )
    test_session.add(completed_booking)
    await test_session.commit()
    
    # Получаем статистику
    zones = await crud.get_zones(test_session)
    
    # Находим нашу зону
    test_zone = next(z for z in zones if z.id == zone.id)
    
    # Проверяем что в статистике только активная бронь
    assert test_zone.active_bookings == 1  # Только active_booking
    assert test_zone.current_occupancy == 1  # Только active_booking (сейчас в зоне)
    
    # Получаем глобальную статистику
    global_stats = await crud.get_global_statistics(test_session)
    
    # Проверяем что завершённые брони не учитываются
    assert global_stats.total_active_bookings == 1
    assert global_stats.users_in_coworking_now == 1
