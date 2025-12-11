from sqlalchemy.orm import Session
from models import Notification
from typing import List

def create_notification(db: Session, user_id: int, type: str, title: str, message: str):
    """Создать уведомление для пользователя"""
    notif = Notification(user_id=user_id, type=type, title=title, message=message)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def get_unsent_notifs(db: Session):
    """Получить список неотправленных уведомлений"""
    return db.query(Notification).filter_by(sent=False).all()

def get_user_notifications(db: Session, user_id: int, limit: int = 50) -> List[Notification]:
    """Получить уведомления пользователя (последние limit штук)"""
    return db.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(limit).all()

def mark_notification_sent(db: Session, notification_id: int):
    """Отметить уведомление как отправленное"""
    notif = db.query(Notification).filter_by(id=notification_id).first()
    if notif:
        notif.sent = True
        db.commit()
        db.refresh(notif)
    return notif