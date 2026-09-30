import os
import hashlib
import secrets
import re
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from models import User, TokenBlacklist

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# 生产环境务必通过环境变量 SECRET_KEY 注入
SECRET_KEY = os.getenv("SECRET_KEY", "crm-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))

# 登录失败锁定配置
MAX_FAILED_ATTEMPTS = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
LOCK_MINUTES = int(os.getenv("LOCK_MINUTES", "15"))

security = HTTPBearer()


def hash_password(password: str) -> str:
    """使用 SHA256 + 盐值进行密码哈希"""
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}{password}".encode()).hexdigest()
    return f"{salt}${h}"


def verify_password(plain: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, h = hashed.split("$", 1)
        return hashlib.sha256(f"{salt}{plain}".encode()).hexdigest() == h
    except (ValueError, AttributeError):
        return False


def validate_password_strength(password: str) -> str:
    """校验密码复杂度，返回错误信息；空字符串表示通过"""
    if len(password) < 8:
        return "密码长度至少 8 位"
    if not re.search(r"[A-Za-z]", password):
        return "密码必须包含字母"
    if not re.search(r"\d", password):
        return "密码必须包含数字"
    return ""


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire, "jti": secrets.token_hex(16)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """解码 token，失败抛 401"""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="无效或过期的认证令牌")


def blacklist_token(db: Session, token: str):
    """将 token 加入黑名单（登出时调用）"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return
    jti = payload.get("jti")
    exp = payload.get("exp")
    if not jti or not exp:
        return
    expires_at = datetime.utcfromtimestamp(exp)
    if not db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        db.add(TokenBlacklist(jti=jti, expires_at=expires_at))
        db.commit()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    payload = decode_token(token)
    user_id: int = payload.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=401, detail="无效的认证令牌")

    # 检查 token 是否已被登出拉黑
    jti = payload.get("jti")
    if jti and db.query(TokenBlacklist).filter(TokenBlacklist.jti == jti).first():
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
