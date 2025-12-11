# services/user-service/set_admin.py
# выполняется после добавления админа как обычного user в бд
from models import User
from config import SessionLocal
from auth import hash_password

if __name__ == "__main__":
    db = SessionLocal()
    user = db.query(User).filter_by(email="admin@punkcrossing.ru").first()
    if user:
        user.name = "admin"
        # Если нужно сменить пароль (можно убрать, если не надо)
        user.hashed_password = hash_password("supersecure")   
        user.role = "admin"
        user.confirmed = True
        db.commit()
        print(f"Пользователь {user.email} — теперь админ!")
    else:
        print("Пользователь не найден.")
    db.close()