from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.account import Account

settings = get_settings()
security = HTTPBearer()


class CurrentUser:
    def __init__(self, id: int, username: str, role: str):
        self.id = id
        self.username = username
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> CurrentUser:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的认证凭据")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token已过期或无效")

    account = db.query(Account).filter(Account.id == int(user_id)).first()
    if not account or account.status == "frozen":
        raise HTTPException(status_code=401, detail="账号不存在或已被冻结")

    return CurrentUser(id=int(user_id), username=username, role=role)


def require_admin(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user


def require_operator(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current_user.role not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="需要运维人员权限")
    return current_user