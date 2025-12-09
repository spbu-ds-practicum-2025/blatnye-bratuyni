from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from mailer import send_email
from schemas import NotificationCreate, BulkEmailNotification, NotificationInternal, NotificationOut
from db import SessionLocal
import crud
import httpx
import os
from typing import List

router = APIRouter()

# URL для получения списка пользователей из user-service
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/notify/email")
async def notify_email(notification: NotificationCreate):
    """// уведомления: Отправить email конкретному пользователю"""
    result = send_email(notification)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"status": "sent"}

@router.post("/notify/bulk")
async def notify_bulk(notification: BulkEmailNotification):
    """// уведомления: Массовая рассылка email всем пользователям (для админа)"""
    try:
        # Получаем список всех пользователей из user-service
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{USER_SERVICE_URL}/users/")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch users")
            users = response.json()
        
        # Отправляем email каждому пользователю
        sent_count = 0
        failed_count = 0
        for user in users:
            email_data = NotificationCreate(
                email=user["email"],
                subject=notification.subject,
                text=notification.text
            )
            result = send_email(email_data)
            if result:
                sent_count += 1
            else:
                failed_count += 1
        
        return {
            "status": "completed",
            "sent": sent_count,
            "failed": failed_count,
            "total": len(users)
        }
    except HTTPException:
        raise
    except Exception as e:
        # Логируем полную ошибку для отладки
        print(f"Bulk email error: {str(e)}")
        raise HTTPException(status_code=500, detail="Bulk email failed")

@router.post("/notify/push")
async def notify_push(notification: NotificationInternal, db: Session = Depends(get_db)):
    """// push: Создать внутреннее push-уведомление для пользователя"""
    try:
        notif = crud.create_notification(
            db=db,
            user_id=notification.user_id,
            type=notification.type,
            title=notification.title,
            message=notification.message
        )
        # В будущем здесь можно добавить отправку через websocket
        return {"status": "created", "notification_id": notif.id}
    except Exception as e:
        # Логируем полную ошибку для отладки
        print(f"Push notification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Push notification failed")

@router.get("/notify/user/{user_id}", response_model=List[NotificationOut])
async def get_user_notifications_endpoint(user_id: int, db: Session = Depends(get_db)):
    """// уведомления: Получить список уведомлений для пользователя"""
    try:
        notifications = crud.get_user_notifications(db=db, user_id=user_id)
        return notifications
    except Exception as e:
        # Логируем полную ошибку для отладки
        print(f"Failed to fetch notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch notifications")