from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class RoleEnum(str, Enum):
    admin = "admin"
    operator = "operator"
    user = "user"


class StatusEnum(str, Enum):
    active = "active"
    frozen = "frozen"


class AccountCreate(BaseModel):
    employee_id: str = Field(..., min_length=1, max_length=32)
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=64)
    department: Optional[str] = Field(None, max_length=128)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    role: RoleEnum = Field(default=RoleEnum.user)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    department: Optional[str] = Field(None, max_length=128)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[RoleEnum] = None


class AccountResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class AccountProfileUpdate(BaseModel):
    """用户修改自己的资料（不含角色）"""
    name: Optional[str] = Field(None, max_length=64)
    department: Optional[str] = Field(None, max_length=128)
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)


class AccountChangePassword(BaseModel):
    """用户修改自己的密码"""
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class AccountResponse(BaseModel):
    id: int
    employee_id: str
    username: str
    name: str
    department: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    status: str
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccountListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AccountResponse]