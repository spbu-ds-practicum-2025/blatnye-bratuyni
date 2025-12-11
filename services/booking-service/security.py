# services/booking-service/app/security.py

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel


class CurrentUser(BaseModel):
    user_id: int
    role: str  # "user" или "admin"


async def get_current_user(
    x_user_id: Optional[int] = Header(default=None, alias="X-User-Id"),
    x_user_role: Optional[str] = Header(default=None, alias="X-User-Role"),
) -> CurrentUser:
    """
    ВРЕМЕННАЯ логика аутентификации для Booking Service.

    Предполагаем, что API Gateway (или какой-то внешний слой)
    уже провалидировал JWT и прокинул нам:
      - X-User-Id  : id пользователя
      - X-User-Role: "user" или "admin"

    Если заголовков нет → 401 Unauthorized.
    Если роль не user/admin → 403 Forbidden.
    """
    if x_user_id is None or x_user_role is None:
        # Нет нужных заголовков — считаем, что пользователь не аутентифицирован
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication headers (X-User-Id / X-User-Role)",
        )

    role_normalized = x_user_role.lower()

    if role_normalized not in {"user", "admin"}:
        # Роль какая-то странная — не пускаем
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role",
        )

    return CurrentUser(user_id=x_user_id, role=role_normalized)


async def get_current_user_id(
    user: CurrentUser = Depends(get_current_user),
) -> int:
    """
    Удобный helper: во всех пользовательских ручках бронирования
    можно просто зависеть от user_id.
    """
    return user.user_id


async def require_admin(
    user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Зависимость для админских ручек.
    Если роль не admin → 403.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    # Если всё ок, просто возвращаем None — факт, что проверка пройдена
    return None
