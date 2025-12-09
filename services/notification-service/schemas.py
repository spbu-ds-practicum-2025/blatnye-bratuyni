from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List

class NotificationCreate(BaseModel):
    email: EmailStr
    subject: str
    text: str

# Схема для массовой рассылки email всем пользователям
class BulkEmailNotification(BaseModel):
    subject: str
    text: str

# Схема для внутреннего push-уведомления
class NotificationInternal(BaseModel):
    user_id: int
    type: str
    title: str
    message: str

# Схема для получения уведомлений пользователя
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    type: str
    title: str
    message: str
    sent: bool
    created_at: str