from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.models.account import Account
from app.schemas.account import (
    AccountCreate, AccountUpdate, AccountResetPassword,
    AccountResponse, AccountListResponse
)
from app.utils.security import hash_password
from app.utils.response import success
from app.middleware.auth import get_current_user, require_admin, CurrentUser

router = APIRouter(prefix="/api/accounts", tags=["账号管理"])


@router.post("", summary="创建运维账号")
def create_account(
    req: AccountCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    existing = db.query(Account).filter(
        or_(Account.employee_id == req.employee_id, Account.username == req.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="工号或用户名已存在")

    account = Account(
        employee_id=req.employee_id,
        username=req.username,
        password_hash=hash_password(req.password),
        name=req.name,
        department=req.department,
        email=req.email,
        phone=req.phone,
        role=req.role.value
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    return success(data=AccountResponse.model_validate(account), message="创建成功")


@router.get("", summary="查询账号列表")
def list_accounts(
    employee_id: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    query = db.query(Account)

    if employee_id:
        query = query.filter(Account.employee_id == employee_id)
    if name:
        query = query.filter(Account.name.like(f"%{name}%"))
    if department:
        query = query.filter(Account.department == department)
    if status:
        query = query.filter(Account.status == status)

    total = query.count()
    items = query.order_by(Account.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return success(data=AccountListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AccountResponse.model_validate(item) for item in items]
    ))


@router.get("/{account_id}", summary="查询单个账号")
def get_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    return success(data=AccountResponse.model_validate(account))


@router.put("/{account_id}", summary="修改账号信息")
def update_account(
    account_id: int,
    req: AccountUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(account, field, value.value if hasattr(value, 'value') else value)

    db.commit()
    db.refresh(account)
    return success(data=AccountResponse.model_validate(account), message="修改成功")


@router.patch("/{account_id}/freeze", summary="冻结账号")
def freeze_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    account.status = "frozen"
    db.commit()
    return success(message="账号已冻结")


@router.patch("/{account_id}/unfreeze", summary="解冻账号")
def unfreeze_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    account.status = "active"
    db.commit()
    return success(message="账号已解冻")


@router.patch("/{account_id}/reset-password", summary="重置密码")
def reset_password(
    account_id: int,
    req: AccountResetPassword,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin)
):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    account.password_hash = hash_password(req.new_password)
    db.commit()
    return success(message="密码已重置")