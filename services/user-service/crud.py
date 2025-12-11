from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError  # // обработка уникальности email
from models import User
from auth import hash_password
from email_utils import generate_code, send_email
from typing import List

def create_user(db: Session, name: str, email: str, password: str):
    # // обработка уникальности: оборачиваем в try-except для IntegrityError на случай race condition
    try:
        code = generate_code()
        user = User(
            name=name,
            email=email,
            hashed_password=hash_password(password),
            confirmation_code=code
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        send_email(email, "Email confirmation", f"Your code: {code}")

        return user
    except IntegrityError:
        # // обработка уникальности: при конкурентном создании пользователей с одинаковым email
        db.rollback()
        raise ValueError("Email already registered")

def confirm_user(db: Session, email: str, code: str):
    user = db.query(User).filter(User.email == email).first()
    if user and user.confirmation_code == code:
        user.confirmed = True
        user.confirmation_code = None
        db.commit()
        return True
    return False

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int):
    """Получить пользователя по ID"""
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session) -> List[User]:
    """Получить всех подтверждённых пользователей (для массовой рассылки)"""
    return db.query(User).filter(User.confirmed == True).all()

def create_recovery_code(db: Session, email: str):
    user = get_user_by_email(db, email)
    if not user:
        return False
    code = generate_code()
    user.recovery_code = code
    db.commit()

    send_email(email, "Password recovery", f"Your code: {code}")
    return True

def reset_password(db: Session, email: str, code: str, new_password: str):
    user = get_user_by_email(db, email)
    if user and user.recovery_code == code:
        user.hashed_password = hash_password(new_password)
        user.recovery_code = None
        db.commit()
        return True
    return False
