from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models.account import Account
from app.utils.security import verify_password, create_access_token
from app.utils.response import success

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    name: str
    role: str


@router.post("/login", summary="用户登录")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.username == req.username).first()
    if not account:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if not verify_password(req.password, account.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    if account.status == "frozen":
        raise HTTPException(status_code=403, detail="账号已被冻结")

    account.last_login_at = datetime.now()
    db.commit()

    token = create_access_token(data={
        "sub": str(account.id),
        "username": account.username,
        "role": account.role
    })

    return success(data=LoginResponse(
        access_token=token,
        user_id=account.id,
        username=account.username,
        name=account.name,
        role=account.role
    ))