from fastapi import APIRouter, Request, Response
import requests
from config import USER_SERVICE_URL

router = APIRouter()

@router.post("/register")
async def register(request: Request):
    body = await request.json()
    resp = requests.post(f"{USER_SERVICE_URL}/users/register", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.post("/login")
async def login(request: Request):
    body = await request.json()
    resp = requests.post(f"{USER_SERVICE_URL}/users/login", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.post("/confirm")
async def confirm(request: Request):
    body = await request.json()
    resp = requests.post(f"{USER_SERVICE_URL}/users/confirm", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.post("/recover")
async def recover(request: Request):
    body = await request.json()
    resp = requests.post(f"{USER_SERVICE_URL}/users/recover", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))

@router.post("/reset")
async def reset(request: Request):
    body = await request.json()
    resp = requests.post(f"{USER_SERVICE_URL}/users/reset", json=body)
    return Response(content=resp.content, status_code=resp.status_code, media_type=resp.headers.get('content-type',"application/json"))