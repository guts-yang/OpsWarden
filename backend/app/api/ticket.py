from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models.ticket import Ticket, TicketLog
from app.schemas.ticket import (
    TicketAutoCreate, TicketUpdate, TicketResolve, TicketCallback,
    TicketResponse, TicketListResponse, TicketLogResponse
)
from app.middleware.auth import get_current_user, require_operator, CurrentUser
from app.utils.response import success

router = APIRouter(prefix="/api/tickets", tags=["工单管理"])


def generate_ticket_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"T-{today}-"
    last_ticket = db.query(Ticket).filter(
        Ticket.ticket_no.like(f"{prefix}%")
    ).order_by(Ticket.ticket_no.desc()).first()

    if last_ticket:
        last_num = int(last_ticket.ticket_no.split("-")[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    return f"{prefix}{new_num:03d}"


def add_log(db: Session, ticket_id: int, action: str,
            operator_id: int = None, operator_name: str = None, content: str = None):
    log = TicketLog(
        ticket_id=ticket_id,
        action=action,
        operator_id=operator_id,
        operator_name=operator_name,
        content=content
    )
    db.add(log)


# OPS-14: AI自动生成工单
@router.post("/auto", summary="AI自动生成工单（RAG无答案时调用）")
def auto_create_ticket(req: TicketAutoCreate, db: Session = Depends(get_db)):
    ticket = Ticket(
        ticket_no=generate_ticket_no(db),
        title=req.title,
        description=req.description or req.title,
        source=req.source.value,
        status="pending",
        priority="medium",
        reporter_name=req.reporter_name
    )
    db.add(ticket)
    db.flush()

    add_log(db, ticket.id, action="created", content=f"AI自动生成工单：{req.title}")
    db.commit()
    db.refresh(ticket)

    return success(data=TicketResponse.model_validate(ticket), message="工单已自动创建")


# OPS-15: 查询工单列表
@router.get("", summary="查询工单列表")
def list_tickets(
    status: Optional[str] = Query(None),
    assignee_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    query = db.query(Ticket)
    if status:
        query = query.filter(Ticket.status == status)
    if assignee_id:
        query = query.filter(Ticket.assignee_id == assignee_id)
    if keyword:
        query = query.filter(Ticket.title.like(f"%{keyword}%"))

    total = query.count()
    items = query.order_by(Ticket.created_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return success(data=TicketListResponse(
        total=total, page=page, page_size=page_size,
        items=[TicketResponse.model_validate(t) for t in items]
    ))


# 查询单个工单
@router.get("/{ticket_id}", summary="查询工单详情")
def get_ticket(ticket_id: int, db: Session = Depends(get_db),
               current_user: CurrentUser = Depends(get_current_user)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    return success(data=TicketResponse.model_validate(ticket))


# 查询工单日志
@router.get("/{ticket_id}/logs", summary="查询工单操作日志")
def get_ticket_logs(ticket_id: int, db: Session = Depends(get_db),
                    current_user: CurrentUser = Depends(get_current_user)):
    logs = db.query(TicketLog).filter(TicketLog.ticket_id == ticket_id) \
             .order_by(TicketLog.created_at.asc()).all()
    return success(data=[TicketLogResponse.model_validate(log) for log in logs])


# 更新工单
@router.put("/{ticket_id}", summary="更新工单")
def update_ticket(ticket_id: int, req: TicketUpdate, db: Session = Depends(get_db),
                  current_user: CurrentUser = Depends(require_operator)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    update_data = req.model_dump(exclude_unset=True)
    log_content = []
    for field, value in update_data.items():
        if value is not None:
            old_value = getattr(ticket, field)
            new_value = value.value if hasattr(value, 'value') else value
            setattr(ticket, field, new_value)
            log_content.append(f"{field}: {old_value} -> {new_value}")

    if log_content:
        add_log(db, ticket.id, action="updated",
                operator_id=current_user.id,
                operator_name=current_user.username,
                content="；".join(log_content))
    db.commit()
    db.refresh(ticket)
    return success(data=TicketResponse.model_validate(ticket), message="更新成功")


# 解决工单
@router.post("/{ticket_id}/resolve", summary="解决工单")
def resolve_ticket(ticket_id: int, req: TicketResolve, db: Session = Depends(get_db),
                   current_user: CurrentUser = Depends(require_operator)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    if ticket.status == "closed":
        raise HTTPException(status_code=400, detail="工单已关闭")

    ticket.status = "resolved"
    ticket.solution = req.solution
    ticket.resolved_at = datetime.now()
    ticket.assignee_id = current_user.id

    add_log(db, ticket.id, action="resolved",
            operator_id=current_user.id,
            operator_name=current_user.username,
            content=f"解决方案：{req.solution}")

    if req.write_back:
        ticket.is_written_back = 1
        add_log(db, ticket.id, action="writeback",
                operator_id=current_user.id,
                operator_name=current_user.username,
                content="解决方案已标记回写知识库")

    db.commit()
    db.refresh(ticket)
    return success(data=TicketResponse.model_validate(ticket), message="工单已解决")


# 回访工单
@router.post("/{ticket_id}/callback", summary="回访工单")
def callback_ticket(ticket_id: int, req: TicketCallback, db: Session = Depends(get_db),
                    current_user: CurrentUser = Depends(require_operator)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    if ticket.status != "resolved":
        raise HTTPException(status_code=400, detail="只能回访已解决的工单")

    ticket.callback_note = req.callback_note
    ticket.callback_at = datetime.now()

    add_log(db, ticket.id, action="callback",
            operator_id=current_user.id,
            operator_name=current_user.username,
            content=f"回访备注：{req.callback_note}")
    db.commit()
    db.refresh(ticket)
    return success(data=TicketResponse.model_validate(ticket), message="回访完成")


# 关闭工单
@router.post("/{ticket_id}/close", summary="关闭工单")
def close_ticket(ticket_id: int, db: Session = Depends(get_db),
                 current_user: CurrentUser = Depends(require_operator)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")

    ticket.status = "closed"
    ticket.closed_at = datetime.now()

    add_log(db, ticket.id, action="closed",
            operator_id=current_user.id,
            operator_name=current_user.username,
            content="工单已关闭")
    db.commit()
    return success(message="工单已关闭")