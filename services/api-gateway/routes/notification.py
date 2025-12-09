from fastapi import APIRouter, Request, Response, Depends
import requests
from config import NOTIFICATION_SERVICE_URL
from auth import get_current_user

router = APIRouter()

@router.post("/")
async def notify(request: Request):
    """// уведомления: Прокси для отправки обычных уведомлений"""
    body = await request.json()
    resp = requests.post(f"{NOTIFICATION_SERVICE_URL}/notify", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.post("/bulk")
async def bulk_notify(request: Request, user=Depends(get_current_user)):
    """// уведомления: Массовая рассылка всем пользователям (только для админов)"""
    # Проверяем, что пользователь - администратор
    if user.get("role") != "admin":
        return Response(
            content='{"detail": "Недостаточно прав"}',
            status_code=403,
            media_type="application/json"
        )
    
    body = await request.json()
    resp = requests.post(f"{NOTIFICATION_SERVICE_URL}/notify/bulk", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.get("/user/{user_id}")
async def get_user_notifications(user_id: int, user=Depends(get_current_user)):
    """// уведомления: Получить уведомления пользователя"""
    # Пользователь может получать только свои уведомления, админ - любые
    if user.get("user_id", user.get("sub")) != user_id and user.get("role") != "admin":
        return Response(
            content='{"detail": "Недостаточно прав"}',
            status_code=403,
            media_type="application/json"
        )
    
    resp = requests.get(f"{NOTIFICATION_SERVICE_URL}/notify/user/{user_id}")
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.options("/bulk")
async def options_bulk():
    """CORS preflight для массовой рассылки"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )

@router.options("/user/{user_id}")
async def options_user_notifications(user_id: int):
    """CORS preflight для получения уведомлений пользователя"""
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "http://localhost:3000",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true"
        }
    )