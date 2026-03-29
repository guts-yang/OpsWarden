from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from app.database import get_db
from app.models.account import Account
from app.models.ticket import Ticket
from app.models.knowledge import KBEntry
from app.middleware.auth import get_current_user, CurrentUser
from app.utils.response import success

router = APIRouter(prefix="/api/analytics", tags=["数据统计"])


@router.get("/summary", summary="仪表盘统计数据")
def get_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago    = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    overdue_threshold = now - timedelta(hours=48)

    daily_qa = db.query(func.count(Ticket.id)).filter(
        Ticket.source == "ai_auto",
        Ticket.created_at >= today_start,
    ).scalar() or 0

    pending_tickets = db.query(func.count(Ticket.id)).filter(
        Ticket.status == "pending"
    ).scalar() or 0

    overdue_count = db.query(func.count(Ticket.id)).filter(
        Ticket.status == "pending",
        Ticket.created_at <= overdue_threshold,
    ).scalar() or 0

    total_accounts = db.query(func.count(Account.id)).scalar() or 0

    new_accounts_month = db.query(func.count(Account.id)).filter(
        Account.created_at >= month_start
    ).scalar() or 0

    kb_entries = db.query(func.count(KBEntry.id)).scalar() or 0

    kb_new_week = db.query(func.count(KBEntry.id)).filter(
        KBEntry.created_at >= week_ago
    ).scalar() or 0

    return success(data={
        "daily_qa":          daily_qa,
        "pending_tickets":   pending_tickets,
        "overdue_count":     overdue_count,
        "total_accounts":    total_accounts,
        "new_accounts_month": new_accounts_month,
        "kb_entries":        kb_entries,
        "kb_new_week":       kb_new_week,
    })
