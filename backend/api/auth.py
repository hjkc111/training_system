# api/auth.py
from fastapi import APIRouter, HTTPException, Body
from datetime import datetime, timedelta
import jwt
import os
from config import FAKE_USERS
from models import LoginRequest

router = APIRouter(prefix="/api/auth", tags=["公共-认证模块"])

@router.post("/login")
async def login(login_data: LoginRequest = Body(...)):
    # 复制你原main.py中登录接口的所有代码（完全不变）
    username = login_data.username
    password = login_data.password
    role = login_data.role
    
    if username not in FAKE_USERS:
        raise HTTPException(status_code=400, detail="用户名不存在")
    user = FAKE_USERS[username]
    if user["password"] != password or user["role"] != role:
        raise HTTPException(status_code=400, detail="密码或身份错误")
    
    expire_minutes = int(os.getenv("JWT_EXPIRE_MINUTES", 60))
    expire = datetime.utcnow() + timedelta(minutes=expire_minutes)
    jwt_secret = os.getenv("JWT_SECRET_KEY", "default_secret_key_for_test")
    token = jwt.encode(
        {"sub": username, "role": role, "exp": expire},
        jwt_secret,
        algorithm="HS256"
    )
    
    return {
        "code": 200,
        "message": "登录成功",
        "token": token,
        "user_info": {"username": username, "role": role}
    }