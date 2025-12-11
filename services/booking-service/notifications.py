import httpx
import os

NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8003")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")

async def get_user_email(user_id: int) -> str:
    """Получить email пользователя из user-service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_SERVICE_URL}/users/{user_id}")
            if response.status_code == 200:
                user_data = response.json()
                return user_data.get("email", "")
    except Exception as e:
        print(f"Failed to fetch user email: {e}")
    return ""

async def send_email_notification(email: str, subject: str, text: str):
    """// уведомления: Отправить email уведомление через notification-service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notify/email",
                json={
                    "email": email,
                    "subject": subject,
                    "text": text,
                }
            )
    except Exception as e:
        # Логируем ошибку, но не прерываем основной процесс
        print(f"Failed to send email notification: {e}")

async def send_push_notification(user_id: int, title: str, message: str, notif_type: str = "info"):
    """// push: Отправить push-уведомление через notification-service"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notify/push",
                json={
                    "user_id": user_id,
                    "type": notif_type,
                    "title": title,
                    "message": message,
                }
            )
    except Exception as e:
        # Логируем ошибку, но не прерываем основной процесс
        print(f"Failed to send push notification: {e}")

async def notify_booking_created(user_id: int, zone_name: str, start_time, end_time):
    """// уведомления: Отправить уведомление о создании бронирования"""
    try:
        user_email = await get_user_email(user_id)
        if user_email:
            await send_email_notification(
                email=user_email,
                subject="Бронирование создано",
                text=f"Ваше бронирование в зоне '{zone_name}' успешно создано.\n"
                     f"Время: {start_time} - {end_time}"
            )
        await send_push_notification(
            user_id=user_id,
            title="Бронирование создано",
            message=f"Бронирование в зоне '{zone_name}' создано",
            notif_type="booking_created"
        )
    except Exception as e:
        print(f"Failed to send booking created notifications: {e}")

async def notify_booking_cancelled(user_id: int, zone_name: str, start_time, end_time):
    """// уведомления: Отправить уведомление об отмене бронирования"""
    try:
        user_email = await get_user_email(user_id)
        if user_email:
            await send_email_notification(
                email=user_email,
                subject="Бронирование отменено",
                text=f"Ваше бронирование в зоне '{zone_name}' было отменено.\n"
                     f"Время: {start_time} - {end_time}"
            )
        await send_push_notification(
            user_id=user_id,
            title="Бронирование отменено",
            message=f"Бронирование в зоне '{zone_name}' отменено",
            notif_type="booking_cancelled"
        )
    except Exception as e:
        print(f"Failed to send booking cancelled notifications: {e}")

async def notify_booking_extended(user_id: int, zone_name: str, end_time):
    """// уведомления: Отправить уведомление о продлении бронирования"""
    try:
        user_email = await get_user_email(user_id)
        if user_email:
            await send_email_notification(
                email=user_email,
                subject="Бронирование продлено",
                text=f"Ваше бронирование в зоне '{zone_name}' успешно продлено.\n"
                     f"Новое время окончания: {end_time}"
            )
        await send_push_notification(
            user_id=user_id,
            title="Бронирование продлено",
            message=f"Бронирование в зоне '{zone_name}' продлено",
            notif_type="booking_extended"
        )
    except Exception as e:
        print(f"Failed to send booking extended notifications: {e}")

async def notify_zone_closed(user_id: int, zone_name: str, reason: str, start_time, end_time):
    """// уведомления: Отправить уведомление о закрытии зоны"""
    try:
        user_email = await get_user_email(user_id)
        if user_email:
            await send_email_notification(
                email=user_email,
                subject="Зона закрыта - бронирование отменено",
                text=f"Зона '{zone_name}' закрыта на обслуживание.\n"
                     f"Причина: {reason}\n"
                     f"Ваше бронирование было автоматически отменено.\n"
                     f"Время: {start_time} - {end_time}"
            )
        await send_push_notification(
            user_id=user_id,
            title="Зона закрыта",
            message=f"Зона '{zone_name}' закрыта. Бронирование отменено",
            notif_type="zone_closed"
        )
    except Exception as e:
        print(f"Failed to send zone closed notifications: {e}")