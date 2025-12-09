from __future__ import annotations

from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    Path,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case, and_

import crud
import schemas
import models
from db import get_session
from security import require_admin
from timezone_utils import now_msk, msk_to_utc

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get(
    "/zones",
    response_model=List[schemas.ZoneOut],
    summary="Получить все зоны (включая закрытые) с полной статистикой (admin)",
)
async def get_all_zones_endpoint(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    return await crud.get_zones(session=session, include_inactive=True)

async def calc_zone_stats(session: AsyncSession, zone_id: int):
    now = msk_to_utc(now_msk())
    stmt = (
        select(
            func.count(case((models.Booking.status == "active", 1))).label("active_bookings"),
            func.count(case((models.Booking.status == "cancelled", 1))).label("cancelled_bookings"),
            func.count(
                case(
                    (
                        and_(
                            models.Booking.status == "active",
                            models.Booking.start_time <= now,
                            models.Booking.end_time > now,
                        ),
                        1
                    )
                )
            ).label("current_occupancy"),
        )
        .select_from(models.Zone)
        .outerjoin(models.Place, models.Place.zone_id == models.Zone.id)
        .outerjoin(models.Slot, models.Slot.place_id == models.Place.id)
        .outerjoin(models.Booking, models.Booking.slot_id == models.Slot.id)
        .where(models.Zone.id == zone_id)
        .group_by(models.Zone.id)
    )

    result = await session.execute(stmt)
    row = result.first()
    if row:
        return dict(
            active_bookings=row.active_bookings or 0,
            cancelled_bookings=row.cancelled_bookings or 0,
            current_occupancy=row.current_occupancy or 0,
        )
    else:
        return dict(
            active_bookings=0,
            cancelled_bookings=0,
            current_occupancy=0,
        )

@router.post(
    "/zones",
    response_model=schemas.ZoneOut,
    status_code=status.HTTP_201_CREATED,
    summary="Создать зону (admin)",
)
async def create_zone_endpoint(
    data: schemas.ZoneCreate,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    zone = await crud.create_zone(session=session, data=data)
    stats = await calc_zone_stats(session, zone.id)
    return schemas.ZoneOut(
        id=zone.id,
        name=zone.name,
        address=zone.address,
        is_active=zone.is_active,
        closure_reason=zone.closure_reason,
        closed_until=zone.closed_until,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
        **stats
    )

@router.patch(
    "/zones/{zone_id}",
    response_model=schemas.ZoneOut,
    summary="Обновить зону (admin)",
)
async def update_zone_endpoint(
    zone_id: int = Path(..., description="ID зоны"),
    data: schemas.ZoneUpdate = ...,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    zone = await crud.update_zone(
        session=session,
        zone_id=zone_id,
        data=data,
    )
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Зона не найдена",
        )
    stats = await calc_zone_stats(session, zone.id)
    return schemas.ZoneOut(
        id=zone.id,
        name=zone.name,
        address=zone.address,
        is_active=zone.is_active,
        closure_reason=zone.closure_reason,
        closed_until=zone.closed_until,
        created_at=zone.created_at,
        updated_at=zone.updated_at,
        **stats
    )

@router.delete(
    "/zones/{zone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить зону (admin)",
)
async def delete_zone_endpoint(
    zone_id: int = Path(..., description="ID зоны"),
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    ok = await crud.delete_zone(session=session, zone_id=zone_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Зона не найдена",
        )
    return

@router.post(
    "/zones/{zone_id}/close",
    response_model=List[schemas.BookingOut],
    summary="Закрыть зону на обслуживание (admin)",
)
async def close_zone_endpoint(
    zone_id: int = Path(..., description="ID зоны"),
    data: schemas.ZoneCloseRequest = ...,
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    affected_bookings = await crud.close_zone(
        session=session,
        zone_id=zone_id,
        data=data,
    )
    return affected_bookings

@router.get(
    "/statistics",
    response_model=schemas.GlobalStatistics,
    summary="Получить глобальную статистику (admin)",
)
async def get_global_statistics_endpoint(
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_admin),
):
    """
    Получить глобальную статистику по всем бронированиям.
    Возвращает количество активных и отменённых бронирований,
    а также количество пользователей в коворкинге прямо сейчас.
    """
    return await crud.get_global_statistics(session)