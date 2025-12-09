from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select, and_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError  # // обработка уникальности и конкурентного доступа

import models
import schemas
from config import settings
from timezone_utils import now_msk, msk_to_utc
from notifications import (
    get_user_email, 
    send_email_notification, 
    send_push_notification,
    notify_booking_created,
    notify_booking_cancelled,
    notify_booking_extended,
    notify_zone_closed
)

# ============================================================
#                    ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

async def auto_complete_expired_bookings(
    session: AsyncSession,
    booking: Optional[models.Booking] = None,
) -> None:
    """
    Автоматически переводит активные бронирования в статус "completed" 
    если их слот уже истёк (end_time < now).
    
    Если передано конкретное бронирование, проверяет только его.
    Иначе проверяет все активные бронирования.
    """
    # // получаем текущее время в UTC (naive datetime для сравнения с БД)
    now = msk_to_utc(now_msk())
    
    if booking:
        # Проверяем только конкретное бронирование
        if booking.status == "active" and booking.end_time is not None:
            # // приводим end_time к naive UTC для корректного сравнения
            end_time_naive = booking.end_time.replace(tzinfo=None) if booking.end_time.tzinfo is not None else booking.end_time
            if end_time_naive <= now:
                booking.status = "completed"
                await session.commit()
    else:
        # Проверяем все активные бронирования
        stmt = (
            select(models.Booking)
            .where(
                and_(
                    models.Booking.status == "active",
                    models.Booking.end_time.isnot(None),
                    models.Booking.end_time <= now,
                )
            )
        )
        result = await session.execute(stmt)
        expired_bookings = list(result.scalars().all())
        
        for exp_booking in expired_bookings:
            exp_booking.status = "completed"
        
        if expired_bookings:
            await session.commit()

# ============================================================
#                       READ-ONLY ЧАСТЬ
# ============================================================

async def get_zones(session: AsyncSession, include_inactive: bool = False) -> List[schemas.ZoneOut]:
    # // автоматически завершаем истёкшие бронирования перед расчётом статистики
    await auto_complete_expired_bookings(session)
    
    now = msk_to_utc(now_msk())
    stmt_reactivate = (
        select(models.Zone)
        .where(
            and_(
                models.Zone.is_active.is_(False),
                models.Zone.closed_until.isnot(None),
                models.Zone.closed_until <= now,
            )
        )
    )
    result = await session.execute(stmt_reactivate)
    zones_to_reactivate = list(result.scalars().all())
    
    for zone in zones_to_reactivate:
        zone.is_active = True
        zone.closure_reason = None
        zone.closed_until = None
    
    if zones_to_reactivate:
        await session.commit()
    
    if include_inactive:
        stmt = select(models.Zone).order_by(models.Zone.name)
    else:
        stmt = (
            select(models.Zone)
            .where(models.Zone.is_active.is_(True))
            .order_by(models.Zone.name)
        )
    result = await session.execute(stmt)
    zones: List[models.Zone] = list(result.scalars().all())

    all_zone_ids = [zone.id for zone in zones]

    stmt_stats = (
        select(
            models.Zone.id.label('zone_id'),
            func.count(case((models.Booking.status == "active", 1))).label("active_bookings"),
            func.count(case((models.Booking.status == "cancelled", 1))).label("cancelled_bookings"),
            func.count(case(
                (
                    and_(
                        models.Booking.status == "active",
                        models.Booking.start_time <= now,
                        models.Booking.end_time > now,
                        models.Place.zone_id == models.Zone.id,
                    ),
                    1
                )
            )).label("current_occupancy"),
        )
        .outerjoin(models.Place, models.Place.zone_id == models.Zone.id)
        .outerjoin(models.Slot, models.Slot.place_id == models.Place.id)
        .outerjoin(models.Booking, models.Booking.slot_id == models.Slot.id)
        .where(models.Zone.id.in_(all_zone_ids))
        .group_by(models.Zone.id)
    )

    result_stats = await session.execute(stmt_stats)
    stats_map = {row.zone_id: row for row in result_stats}

    result_list = []
    for zone in zones:
        stats_row = stats_map.get(zone.id)
        result_list.append(schemas.ZoneOut(
            id=zone.id,
            name=zone.name,
            address=zone.address,
            is_active=zone.is_active,
            closure_reason=zone.closure_reason,
            closed_until=zone.closed_until,
            created_at=zone.created_at,
            updated_at=zone.updated_at,
            active_bookings=int(getattr(stats_row, "active_bookings", 0)),
            cancelled_bookings=int(getattr(stats_row, "cancelled_bookings", 0)),
            current_occupancy=int(getattr(stats_row, "current_occupancy", 0)),
        ))
    return result_list

async def get_places_by_zone(
    session: AsyncSession,
    zone_id: int,
) -> List[models.Place]:
    stmt = (
        select(models.Place)
        .where(
            and_(
                models.Place.zone_id == zone_id,
                models.Place.is_active.is_(True),
            )
        )
        .order_by(models.Place.name)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())

async def get_slots_by_place_and_date(
    session: AsyncSession,
    place_id: int,
    target_date: date,
) -> List[models.Slot]:
    date_start = datetime.combine(target_date, datetime.min.time())
    date_end = datetime.combine(target_date, datetime.max.time())
    result = await session.execute(
        select(models.Slot)
        .where(
            and_(
                models.Slot.place_id == place_id,
                models.Slot.start_time >= date_start,
                models.Slot.start_time <= date_end,
            )
        )
        .order_by(models.Slot.start_time)
    )
    return list(result.scalars().all())

# ============================================================
#                      BOOKING ОПЕРАЦИИ
# ============================================================

async def check_user_booking_conflicts(
    session: AsyncSession,
    user_id: int,
    start_time: datetime,
    end_time: datetime,
    exclude_booking_id: Optional[int] = None,
) -> bool:
    stmt = select(models.Booking).where(
        and_(
            models.Booking.user_id == user_id,
            models.Booking.status == "active",
            models.Booking.start_time < end_time,
            models.Booking.end_time > start_time,
        )
    )
    if exclude_booking_id is not None:
        stmt = stmt.where(models.Booking.id != exclude_booking_id)
    result = await session.execute(stmt)
    conflicting_bookings = result.scalars().all()
    return len(conflicting_bookings) > 0

async def create_booking(
    session: AsyncSession,
    user_id: int,
    booking_in: schemas.BookingCreate,
) -> Optional[models.Booking]:
    # // транзакция: используем row-level locking для предотвращения race condition
    # // исправление: убран joinedload для избежания ошибки "FOR UPDATE cannot be applied to the nullable side of an outer join"
    try:
        # // конкурентный доступ: SELECT FOR UPDATE блокирует только Slot без JOIN
        stmt = (
            select(models.Slot)
            .where(models.Slot.id == booking_in.slot_id)
            .with_for_update()  # // row-level lock только на Slot
        )
        result = await session.execute(stmt)
        slot = result.scalar_one_or_none()
        if slot is None:
            return None
        if not slot.is_available:
            return None
        
        # // загружаем place и zone отдельно, после блокировки Slot
        place = None
        zone = None
        if slot.place_id:
            place = await session.get(models.Place, slot.place_id)
            if place and place.zone_id:
                zone = await session.get(models.Zone, place.zone_id)
        stmt = select(models.Booking).where(
            and_(
                models.Booking.user_id == user_id,
                models.Booking.slot_id == slot.id,
                models.Booking.status == "active",
            )
        )
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing is not None:
            return None
        has_conflict = await check_user_booking_conflicts(
            session=session,
            user_id=user_id,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )
        if has_conflict:
            return None
        # // используем уже загруженную zone для проверки вместимости
        if zone:
            can_book = await check_zone_capacity(
                session=session,
                zone_id=zone.id,
                start_time=slot.start_time,
                end_time=slot.end_time,
            )
            if not can_book:
                return None
        # // используем уже полученную zone для создания бронирования
        booking = models.Booking(
            user_id=user_id,
            slot_id=slot.id,
            status="active",
            zone_name=zone.name if zone else None,
            zone_address=zone.address if zone else None,
            start_time=slot.start_time,
            end_time=slot.end_time,
        )
        session.add(booking)
        slot.is_available = False
        # // транзакция: commit гарантирует атомарность всей операции
        await session.commit()
        await session.refresh(booking)
        
        # // уведомления: Отправляем email и push уведомление при создании бронирования
        await notify_booking_created(user_id, booking.zone_name, booking.start_time, booking.end_time)
        
        return booking
    except IntegrityError:
        # // обработка уникальности: ловим IntegrityError при попытке создать дублирующее бронирование
        await session.rollback()
        return None

async def create_booking_by_time_range(
    session: AsyncSession,
    user_id: int,
    booking_in: schemas.BookingCreateTimeRange,
) -> Optional[models.Booking]:
    from datetime import datetime, timedelta, date as date_type
    
    # // обработка уникальности и конкурентного доступа: оборачиваем в try-except для IntegrityError
    try:
        try:
            target_date = date_type.fromisoformat(booking_in.date)
        except ValueError:
            raise BookingError("INVALID_DATE", "Некорректная дата")
        
        start_time = datetime.combine(
            target_date,
            datetime.min.time().replace(
                hour=booking_in.start_hour,
                minute=booking_in.start_minute
            )
        )
        end_time = datetime.combine(
            target_date,
            datetime.min.time().replace(
                hour=booking_in.end_hour,
                minute=booking_in.end_minute
            )
        )
        # // Исправление таймзоны: если API присылает naive datetime (без tzinfo),
        # // считаем его московским временем и конвертируем в UTC для хранения в БД.
        # // Функция msk_to_utc() возвращает naive UTC datetime.
        # // Если API прислал aware datetime - конвертируем в naive UTC для хранения.
        if start_time.tzinfo is None:
            # Naive datetime - считаем московским временем
            start_time = msk_to_utc(start_time)
        else:
            # Aware datetime - конвертируем в naive UTC
            start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
        
        if end_time.tzinfo is None:
            # Naive datetime - считаем московским временем
            end_time = msk_to_utc(end_time)
        else:
            # Aware datetime - конвертируем в naive UTC
            end_time = end_time.astimezone(timezone.utc).replace(tzinfo=None)
        # ----------------------------------------------------------------------
        duration = end_time - start_time
        if duration.total_seconds() <= 0:
            raise BookingError("INVALID_TIME_RANGE", "Некорректный временной интервал: время окончания должно быть позже времени начала")
        if duration.total_seconds() > settings.MAX_BOOKING_HOURS * 3600:
            raise BookingError("TIME_LIMIT_EXCEEDED", f"Превышен лимит времени бронирования: максимум {settings.MAX_BOOKING_HOURS} часов")
        zone = await session.get(models.Zone, booking_in.zone_id)
        if zone is None or not zone.is_active:
            raise BookingError("ZONE_INACTIVE", "Зона недоступна или неактивна")
        has_conflict = await check_user_booking_conflicts(
            session=session,
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )
        if has_conflict:
            raise BookingError("USER_CONFLICT", "У вас уже есть активное бронирование на это время")
        can_book = await check_zone_capacity(
            session=session,
            zone_id=zone.id,
            start_time=start_time,
            end_time=end_time,
        )
        if not can_book:
            raise BookingError("ZONE_CAPACITY_EXCEEDED", "Зона переполнена: достигнута максимальная вместимость")
        stmt = (
            select(models.Place)
            .where(
                and_(
                    models.Place.zone_id == zone.id,
                    models.Place.is_active.is_(True),
                )
            )
        )
        result = await session.execute(stmt)
        places = list(result.scalars().all())
        if not places:
            raise BookingError("NO_AVAILABLE_PLACES", "Нет доступных мест в данной зоне")
        for place in places:
            # // конкурентный доступ: SELECT FOR UPDATE блокирует существующий слот
            stmt_exact = (
                select(models.Slot)
                .where(
                    and_(
                        models.Slot.place_id == place.id,
                        models.Slot.start_time == start_time,
                        models.Slot.end_time == end_time,
                    )
                )
                .with_for_update()  # // row-level lock для атомарности
            )
            result_exact = await session.execute(stmt_exact)
            exact_slot = result_exact.scalar_one_or_none()
            if exact_slot and exact_slot.is_available:
                exact_slot.is_available = False
                booking = models.Booking(
                    user_id=user_id,
                    slot_id=exact_slot.id,
                    status="active",
                    zone_name=zone.name,
                    zone_address=zone.address,
                    start_time=start_time,
                    end_time=end_time,
                )
                session.add(booking)
                # // транзакция: commit гарантирует атомарность
                await session.commit()
                await session.refresh(booking, attribute_names=['slot'])
                
                # // уведомления: Отправляем email и push уведомление при создании бронирования
                await notify_booking_created(user_id, booking.zone_name, booking.start_time, booking.end_time)
                
                return booking
            if exact_slot and not exact_slot.is_available:
                continue
            if not exact_slot:
                stmt = (
                    select(models.Slot)
                    .where(
                        and_(
                            models.Slot.place_id == place.id,
                            models.Slot.start_time < end_time,
                            models.Slot.end_time > start_time,
                        )
                    )
                )
                result = await session.execute(stmt)
                overlapping_slots = list(result.scalars().all())
                has_conflict = False
                for slot in overlapping_slots:
                    if not slot.is_available:
                        has_conflict = True
                        break
                if not has_conflict:
                    # // создаём новый слот - unique constraint на (place_id, start_time, end_time) предотвратит дубли
                    slot = models.Slot(
                        place_id=place.id,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=False,
                    )
                    session.add(slot)
                    await session.flush()
                    booking = models.Booking(
                        user_id=user_id,
                        slot_id=slot.id,
                        status="active",
                        zone_name=zone.name,
                        zone_address=zone.address,
                        start_time=start_time,
                        end_time=end_time,
                    )
                    session.add(booking)
                    # // транзакция: commit гарантирует атомарность
                    await session.commit()
                    await session.refresh(booking, attribute_names=['slot'])
                    
                    # // уведомления: Отправляем email и push уведомление при создании бронирования
                    await notify_booking_created(user_id, booking.zone_name, booking.start_time, booking.end_time)
                    
                    return booking
        # // если все места проверены и ни одно не подошло
        raise BookingError("NO_AVAILABLE_PLACES", "Нет свободных мест на указанное время")
    except IntegrityError:
        # // обработка уникальности: ловим IntegrityError при попытке создать дублирующий слот или бронирование
        await session.rollback()
        raise BookingError("NO_AVAILABLE_PLACES", "Нет свободных мест на указанное время (конфликт при создании)")

async def get_booking_by_id(
    session: AsyncSession,
    booking_id: int,
) -> Optional[models.Booking]:
    # // исправление: добавляем eager-загрузку slot и place для избежания MissingGreenlet
    stmt = (
        select(models.Booking)
        .options(joinedload(models.Booking.slot).joinedload(models.Slot.place))
        .where(models.Booking.id == booking_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()

async def cancel_booking(
    session: AsyncSession,
    user_id: int,
    booking_id: int,
    *,
    is_admin: bool = False,
) -> Optional[models.Booking]:
    # // транзакция и конкурентный доступ: используем SELECT FOR UPDATE для атомарности отмены
    # // исправление: убран joinedload для избежания ошибки "FOR UPDATE cannot be applied to the nullable side of an outer join"
    try:
        # // конкурентный доступ: блокируем только Booking без JOIN, чтобы избежать OUTER JOIN + FOR UPDATE
        stmt = (
            select(models.Booking)
            .where(models.Booking.id == booking_id)
            .with_for_update()  # // row-level lock только на Booking
        )
        result = await session.execute(stmt)
        booking = result.scalar_one_or_none()
        
        if booking is None:
            return None
        # // проверка прав доступа: только владелец или админ может отменить бронь
        if not is_admin and booking.user_id != user_id:
            return None
        if booking.status != "active":
            return booking
        
        # // загружаем slot отдельно, после блокировки Booking
        if booking.slot_id:
            slot = await session.get(models.Slot, booking.slot_id)
            if slot:
                slot.is_available = True
        
        booking.status = "cancelled"
        # // транзакция: commit гарантирует атомарность операции
        await session.commit()
        await session.refresh(booking)
        
        # // уведомления: Отправляем email и push уведомление при отмене бронирования
        await notify_booking_cancelled(booking.user_id, booking.zone_name, booking.start_time, booking.end_time)
        
        return booking
    except IntegrityError:
        # // обработка ошибок БД
        await session.rollback()
        return None

async def get_booking_history(
    session: AsyncSession,
    user_id: int,
    filters: Optional[schemas.BookingHistoryFilters] = None,
) -> List[models.Booking]:
    # // автоматически завершаем истёкшие бронирования перед получением истории
    await auto_complete_expired_bookings(session)
    
    filters = filters or schemas.BookingHistoryFilters()
    # // исправление: добавляем eager-загрузку slot и place для избежания MissingGreenlet
    stmt = (
        select(models.Booking)
        .join(models.Slot, models.Slot.id == models.Booking.slot_id)
        .join(models.Place, models.Place.id == models.Slot.place_id)
        .join(models.Zone, models.Zone.id == models.Place.zone_id)
        .where(models.Booking.user_id == user_id)
        .options(joinedload(models.Booking.slot).joinedload(models.Slot.place))
        .order_by(models.Booking.created_at.desc())
    )
    conds = []
    if filters.status:
        conds.append(models.Booking.status == filters.status)
    if filters.zone_id:
        conds.append(models.Zone.id == filters.zone_id)
    if filters.date_from:
        conds.append(models.Slot.start_time >= filters.date_from)
    if filters.date_to:
        conds.append(models.Slot.start_time <= filters.date_to)
    if conds:
        stmt = stmt.where(and_(*conds))
    result = await session.execute(stmt)
    return list(result.scalars().all())

class BookingExtensionError(Exception):
    """
    Исключение для конкретных ошибок при продлении брони.
    Содержит код ошибки и сообщение для пользователя.
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

# // Класс для детальных ошибок при создании брони
class BookingError(Exception):
    """
    Исключение для конкретных ошибок при создании брони.
    Содержит код ошибки и сообщение для пользователя.
    """
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)

async def extend_booking(
    session: AsyncSession,
    user_id: int,
    booking_id: int,
    extend_hours: int = 1,
    extend_minutes: int = 0,
) -> models.Booking:
    # // транзакция и конкурентный доступ: оборачиваем в try-except для обработки IntegrityError
    # // исправление: убран joinedload для избежания ошибки "FOR UPDATE cannot be applied to the nullable side of an outer join"
    try:
        # // конкурентный доступ: блокируем только Booking без JOIN
        stmt = (
            select(models.Booking)
            .where(models.Booking.id == booking_id)
            .with_for_update()  # // row-level lock только на Booking
        )
        result = await session.execute(stmt)
        booking = result.scalar_one_or_none()
        
        if booking is None:
            raise BookingExtensionError(
                "booking_not_found",
                "Бронирование не найдено"
            )
        
        # // проверка истечения срока: автоматически переводим истёкшие брони в статус "completed"
        now = msk_to_utc(now_msk())
        if booking.end_time:
            # // приводим end_time к naive UTC для корректного сравнения
            end_time_naive = booking.end_time.replace(tzinfo=None) if booking.end_time.tzinfo is not None else booking.end_time
            if end_time_naive <= now:
                # Автоматически завершаем истёкшую бронь
                await auto_complete_expired_bookings(session, booking)
                raise BookingExtensionError(
                    "booking_expired",
                    "Бронирование уже завершено: слот истёк. Создайте новое бронирование."
                )
        
        # // проверка прав доступа: только владелец может продлить бронирование
        if booking.user_id != user_id:
            raise BookingExtensionError(
                "permission_denied",
                "Нет прав на продление этого бронирования"
            )
        if booking.status != "active":
            raise BookingExtensionError(
                "invalid_status",
                "Можно продлить только активное бронирование"
            )
        if booking.start_time is None or booking.end_time is None:
            raise BookingExtensionError(
                "invalid_data",
                "Некорректные данные бронирования"
            )
        
        # // загружаем slot отдельно, после блокировки Booking
        slot = None
        if booking.slot_id:
            slot = await session.get(models.Slot, booking.slot_id)
        if slot is None:
            raise BookingExtensionError(
                "slot_not_found",
                "Слот бронирования не найден"
            )
        new_end_time = booking.end_time + timedelta(hours=extend_hours, minutes=extend_minutes)
        total_duration = new_end_time - booking.start_time
        if total_duration.total_seconds() > settings.MAX_BOOKING_HOURS * 3600:
            raise BookingExtensionError(
                "max_duration_exceeded",
                f"Превышен максимальный лимит бронирования ({settings.MAX_BOOKING_HOURS} часов)"
            )
        has_conflict = await check_user_booking_conflicts(
            session=session,
            user_id=user_id,
            start_time=booking.end_time,
            end_time=new_end_time,
            exclude_booking_id=booking_id,
        )
        if has_conflict:
            raise BookingExtensionError(
                "user_time_conflict",
                "У вас уже есть другое бронирование на это время"
            )
        # // исправление: используем slot.place_id вместо slot.place для избежания lazy-загрузки
        zone = None
        if slot.place_id:
            stmt = (
                select(models.Place)
                .options(joinedload(models.Place.zone))
                .where(models.Place.id == slot.place_id)
            )
            result = await session.execute(stmt)
            place = result.scalar_one_or_none()
            if place and place.zone:
                zone = place.zone
        if zone is None:
            raise BookingExtensionError(
                "zone_not_found",
                "Зона не найдена"
            )
        can_book = await check_zone_capacity(
            session=session,
            zone_id=zone.id,
            start_time=booking.end_time,
            end_time=new_end_time,
        )
        if not can_book:
            raise BookingExtensionError(
                "zone_capacity_exceeded",
                "Зона переполнена на выбранное время. Попробуйте продлить на меньшее время"
            )
        # // конкурентный доступ: SELECT FOR UPDATE для существующего слота
        stmt_exact = (
            select(models.Slot)
            .where(
                and_(
                    models.Slot.place_id == slot.place_id,
                    models.Slot.start_time == booking.end_time,
                    models.Slot.end_time == new_end_time,
                )
            )
            .with_for_update()  # // row-level lock
        )
        result_exact = await session.execute(stmt_exact)
        extended_slot = result_exact.scalar_one_or_none()
        if extended_slot and extended_slot.is_available:
            extended_slot.is_available = False
        elif extended_slot and not extended_slot.is_available:
            raise BookingExtensionError(
                "slot_unavailable",
                "Выбранное время уже занято. Попробуйте продлить на меньшее время"
            )
        else:
            stmt_overlap = (
                select(models.Slot)
                .where(
                    and_(
                        models.Slot.place_id == slot.place_id,
                        models.Slot.start_time < new_end_time,
                        models.Slot.end_time > booking.end_time,
                    )
                )
            )
            result_overlap = await session.execute(stmt_overlap)
            overlapping_slots = list(result_overlap.scalars().all())
            for overlap_slot in overlapping_slots:
                if not overlap_slot.is_available:
                    raise BookingExtensionError(
                        "slot_partially_occupied",
                        "Выбранное время частично занято. Попробуйте продлить на меньшее время"
                    )
            # // создаём новый слот - unique constraint предотвратит дубликацию
            extended_slot = models.Slot(
                place_id=slot.place_id,
                start_time=booking.end_time,
                end_time=new_end_time,
                is_available=False,
            )
            session.add(extended_slot)
            await session.flush()
        new_booking = models.Booking(
            user_id=user_id,
            slot_id=extended_slot.id,
            status="active",
            zone_name=zone.name if zone else None,
            zone_address=zone.address if zone else None,
            start_time=booking.end_time,
            end_time=new_end_time,
        )
        session.add(new_booking)
        # // транзакция: commit гарантирует атомарность всей операции
        await session.commit()
        await session.refresh(new_booking)
        
        # // уведомления: Отправляем email и push уведомление при продлении бронирования
        await notify_booking_extended(user_id, new_booking.zone_name, new_booking.end_time)
        
        return new_booking
    except IntegrityError:
        # // обработка уникальности: ловим IntegrityError при создании дублирующего слота
        await session.rollback()
        raise BookingExtensionError(
            "integrity_error",
            "Не удалось продлить бронирование - возможно, слот уже занят"
        )

# ============================================================
#                      АДМИНСКИЕ ОПЕРАЦИИ
# ============================================================

async def create_zone(
    session: AsyncSession,
    data: schemas.ZoneCreate,
) -> models.Zone:
    zone = models.Zone(
        name=data.name,
        address=data.address,
        is_active=data.is_active,
    )
    session.add(zone)
    await session.flush()
    for i in range(1, data.places_count + 1):
        place = models.Place(
            zone_id=zone.id,
            name=f"Место {i}",
            is_active=True,
        )
        session.add(place)
    await session.commit()
    await session.refresh(zone)
    return zone

async def update_zone(
    session: AsyncSession,
    zone_id: int,
    data: schemas.ZoneUpdate,
) -> Optional[models.Zone]:
    zone = await session.get(models.Zone, zone_id)
    if zone is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(zone, field, value)
    await session.commit()
    await session.refresh(zone)
    return zone

async def delete_zone(
    session: AsyncSession,
    zone_id: int,
) -> bool:
    zone = await session.get(models.Zone, zone_id)
    if zone is None:
        return False
    await session.delete(zone)
    await session.commit()
    return True

async def close_zone(
    session: AsyncSession,
    zone_id: int,
    data: schemas.ZoneCloseRequest,
) -> List[models.Booking]:
    zone = await session.get(models.Zone, zone_id)
    if zone is None:
        return []
    zone.is_active = False
    zone.closure_reason = data.reason
    zone.closed_until = data.to_time
    # // исправление: добавляем eager-загрузку slot и place для избежания MissingGreenlet
    stmt = (
        select(models.Booking)
        .join(models.Slot, models.Slot.id == models.Booking.slot_id)
        .join(models.Place, models.Place.id == models.Slot.place_id)
        .join(models.Zone, models.Zone.id == models.Place.zone_id)
        .where(
            and_(
                models.Zone.id == zone_id,
                models.Booking.status == "active",
                models.Slot.start_time < data.to_time,
                models.Slot.end_time  > data.from_time,
            )
        )
        .options(joinedload(models.Booking.slot).joinedload(models.Slot.place))
    )
    result = await session.execute(stmt)
    affected_bookings: List[models.Booking] = list(result.scalars().all())
    for booking in affected_bookings:
        booking.status = "cancelled"
        booking.cancellation_reason = f"Зона закрыта: {data.reason}"
        if booking.slot:
            booking.slot.is_available = True
    await session.commit()
    await session.refresh(zone)
    for booking in affected_bookings:
        await session.refresh(booking)
    
    # // уведомления: Отправляем email и push уведомление всем затронутым пользователям о закрытии зоны
    for booking in affected_bookings:
        await notify_zone_closed(
            booking.user_id,
            zone.name,
            data.reason,
            booking.start_time,
            booking.end_time
        )
    
    return affected_bookings

async def get_global_statistics(
    session: AsyncSession,
) -> schemas.GlobalStatistics:
    # // автоматически завершаем истёкшие бронирования перед расчётом статистики
    await auto_complete_expired_bookings(session)
    
    stmt = select(
        func.count(models.Booking.id).filter(models.Booking.status == "active").label("active_count"),
        func.count(models.Booking.id).filter(models.Booking.status == "cancelled").label("cancelled_count"),
    )
    result = await session.execute(stmt)
    row = result.one()
    total_active = row.active_count or 0
    total_cancelled = row.cancelled_count or 0
    now = msk_to_utc(now_msk())
    stmt = select(func.count(func.distinct(models.Booking.user_id))).where(
        and_(
            models.Booking.status == "active",
            models.Booking.start_time <= now,
            models.Booking.end_time > now,
        )
    )
    result = await session.execute(stmt)
    users_now = result.scalar() or 0
    return schemas.GlobalStatistics(
        total_active_bookings=total_active,
        total_cancelled_bookings=total_cancelled,
        users_in_coworking_now=users_now,
    )

async def get_zones_statistics(
    session: AsyncSession,
) -> List[schemas.ZoneStatistics]:
    """
    Получить статистику по всем зонам.
    Возвращает статистику для каждой зоны: активные и отменённые брони,
    текущую загрузку (сколько человек сейчас в зоне).
    """
    # // автоматически завершаем истёкшие бронирования перед расчётом статистики
    await auto_complete_expired_bookings(session)
    
    now = msk_to_utc(now_msk())
    
    # Получаем все зоны
    stmt = select(models.Zone).order_by(models.Zone.name)
    result = await session.execute(stmt)
    zones: List[models.Zone] = list(result.scalars().all())
    
    all_zone_ids = [zone.id for zone in zones]
    
    # Получаем статистику по бронированиям
    stmt_stats = (
        select(
            models.Zone.id.label('zone_id'),
            func.count(case((models.Booking.status == "active", 1))).label("active_bookings"),
            func.count(case((models.Booking.status == "cancelled", 1))).label("cancelled_bookings"),
            func.count(case(
                (
                    and_(
                        models.Booking.status == "active",
                        models.Booking.start_time <= now,
                        models.Booking.end_time > now,
                        models.Place.zone_id == models.Zone.id,
                    ),
                    1
                )
            )).label("current_occupancy"),
        )
        .outerjoin(models.Place, models.Place.zone_id == models.Zone.id)
        .outerjoin(models.Slot, models.Slot.place_id == models.Place.id)
        .outerjoin(models.Booking, models.Booking.slot_id == models.Slot.id)
        .where(models.Zone.id.in_(all_zone_ids))
        .group_by(models.Zone.id)
    )
    
    result_stats = await session.execute(stmt_stats)
    stats_map = {row.zone_id: row for row in result_stats}
    
    result_list = []
    for zone in zones:
        stats_row = stats_map.get(zone.id)
        result_list.append(schemas.ZoneStatistics(
            zone_id=zone.id,
            zone_name=zone.name,
            is_active=zone.is_active,
            closure_reason=zone.closure_reason,
            closed_until=zone.closed_until,
            active_bookings=int(getattr(stats_row, "active_bookings", 0)),
            cancelled_bookings=int(getattr(stats_row, "cancelled_bookings", 0)),
            current_occupancy=int(getattr(stats_row, "current_occupancy", 0)),
        ))
    return result_list

async def check_zone_capacity(
    session: AsyncSession,
    zone_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    # // Исправление timezone: приводим start_time и end_time к aware-UTC для корректного сравнения
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)
    
    stmt = select(func.count(models.Place.id)).where(
        and_(
            models.Place.zone_id == zone_id,
            models.Place.is_active.is_(True),
        )
    )
    result = await session.execute(stmt)
    max_capacity = result.scalar() or 0
    if max_capacity == 0:
        return False
    stmt = (
        select(models.Booking)
        .join(models.Slot, models.Slot.id == models.Booking.slot_id)
        .join(models.Place, models.Place.id == models.Slot.place_id)
        .where(
            and_(
                models.Place.zone_id == zone_id,
                models.Booking.status == "active",
                models.Booking.start_time < end_time,
                models.Booking.end_time > start_time,
            )
        )
    )
    result = await session.execute(stmt)
    overlapping_bookings = list(result.scalars().all())
    time_points = []
    time_points.append(start_time)
    time_points.append(end_time)
    for booking in overlapping_bookings:
        if booking.start_time and booking.end_time:
            # // приводим все временные точки бронирований к aware-UTC
            bt_start = booking.start_time.replace(tzinfo=timezone.utc) if booking.start_time.tzinfo is None else booking.start_time
            bt_end = booking.end_time.replace(tzinfo=timezone.utc) if booking.end_time.tzinfo is None else booking.end_time
            time_points.append(bt_start)
            time_points.append(bt_end)
    time_points = sorted(set(time_points))
    for check_time in time_points:
        if check_time < start_time or check_time >= end_time:
            continue
        active_count = 0
        for booking in overlapping_bookings:
            if booking.start_time and booking.end_time:
                # // приводим время бронирования к aware-UTC для корректного сравнения
                b_start = booking.start_time.replace(tzinfo=timezone.utc) if booking.start_time.tzinfo is None else booking.start_time
                b_end = booking.end_time.replace(tzinfo=timezone.utc) if booking.end_time.tzinfo is None else booking.end_time
                if b_start <= check_time < b_end:
                    active_count += 1
        if start_time <= check_time < end_time:
            active_count += 1
        if active_count > max_capacity:
            return False
    return True