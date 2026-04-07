from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum


class DepartmentEnum(str, Enum):
    infra = "infra"
    network_security = "network_security"
    database_middleware = "database_middleware"
    app_ops = "app_ops"
    helpdesk = "helpdesk"
    rnd = "rnd"
    general = "general"


class RoleEnum(str, Enum):
    admin = "admin"
    operator = "operator"
    user = "user"


class StatusEnum(str, Enum):
    active = "active"
    frozen = "frozen"


class AccountCreate(BaseModel):
    """employee_id 省略或为空时由服务端按 role 自动生成；显式传入则校验长度并保证唯一。"""
    employee_id: Optional[str] = Field(None, max_length=32)
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6, max_length=128)
    name: str = Field(..., min_length=1, max_length=64)
    department: Optional[DepartmentEnum] = None
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    role: RoleEnum = Field(default=RoleEnum.user)

    @field_validator("employee_id", mode="before")
    @classmethod
    def employee_id_strip_empty(cls, v):
        if v is None or (isinstance(v, str) and not v.strip()):
            return None
        return v.strip() if isinstance(v, str) else v

    @field_validator("department", mode="before")
    @classmethod
    def department_empty_to_none(cls, v):
        if v is None or v == "":
            return None
        return v


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=64)
    department: Optional[DepartmentEnum] = None
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)
    role: Optional[RoleEnum] = None

    @field_validator("department", mode="before")
    @classmethod
    def department_empty_to_none(cls, v):
        if v is None or v == "":
            return None
        return v


class AccountResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class AccountProfileUpdate(BaseModel):
    """用户修改自己的资料（不含角色）"""
    name: Optional[str] = Field(None, max_length=64)
    department: Optional[DepartmentEnum] = None
    email: Optional[str] = Field(None, max_length=128)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("department", mode="before")
    @classmethod
    def department_empty_to_none(cls, v):
        if v is None or v == "":
            return None
        return v


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