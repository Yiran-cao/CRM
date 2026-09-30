from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserLogin, TokenResponse, UserInfo
from auth import (
    verify_password, create_access_token, get_current_user, blacklist_token,
    security, MAX_FAILED_ATTEMPTS, LOCK_MINUTES,
)

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    # 检查是否处于锁定状态
    if user and user.locked_until and user.locked_until > datetime.now():
        remain = int((user.locked_until - datetime.now()).total_seconds() // 60) + 1
        raise HTTPException(status_code=403, detail=f"登录失败次数过多，请 {remain} 分钟后再试")

    if not user or not verify_password(data.password, user.password_hash):
        # 记录失败次数，达到阈值则锁定
        if user:
            user.failed_attempts = (user.failed_attempts or 0) + 1
            if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.now() + timedelta(minutes=LOCK_MINUTES)
                user.failed_attempts = 0
                db.commit()
                raise HTTPException(status_code=403, detail=f"登录失败次数过多，账户已锁定 {LOCK_MINUTES} 分钟")
            db.commit()
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 登录成功，重置失败计数
    user.failed_attempts = 0
    user.locked_until = None
    db.commit()

    token = create_access_token({"user_id": user.id, "role": user.role})
    return TokenResponse(
        access_token=token,
        user=UserInfo(
            id=user.id,
            name=user.name,
            username=user.username,
            role=user.role,
            dealer_name=user.dealer_name,
        ),
    )


@router.post("/logout")
def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """登出：将当前 token 加入黑名单使其失效"""
    blacklist_token(db, credentials.credentials)
    return {"message": "已退出登录"}
