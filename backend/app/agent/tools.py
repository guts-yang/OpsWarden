from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session

from app.agent.policy import is_operator, normalize_priority, normalize_status
from app.database import engine
from app.middleware.auth import CurrentUser
from app.models.account import Account
from app.models.knowledge import KBEntry
from app.models.ticket import Ticket, TicketLog
from app.rag.retriever import collection_count, search as rag_search


def _generate_ticket_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"T-{today}-"
    last = (
        db.query(Ticket)
        .filter(Ticket.ticket_no.like(f"{prefix}%"))
        .order_by(Ticket.ticket_no.desc())
        .first()
    )
    num = (int(last.ticket_no.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:03d}"


def _ticket_to_dict(ticket: Ticket) -> dict[str, Any]:
    return {
        "id": int(ticket.id),
        "ticket_no": ticket.ticket_no,
        "title": ticket.title,
        "description": ticket.description,
        "source": ticket.source,
        "status": ticket.status,
        "priority": ticket.priority,
        "reporter_id": int(ticket.reporter_id) if ticket.reporter_id else None,
        "reporter_name": ticket.reporter_name,
        "assignee_id": int(ticket.assignee_id) if ticket.assignee_id else None,
        "solution": ticket.solution,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
    }


def kb_search(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query") or "").strip()
    top_k = int(args.get("top_k") or 3)
    top_k = max(1, min(top_k, 5))
    if not query:
        return {"ok": False, "error": "query is required", "items": []}
    items = rag_search(query, top_k=top_k)
    return {"ok": True, "items": items, "count": len(items)}


def ticket_search(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    if not is_operator(user):
        return {"ok": False, "error": "permission denied", "items": []}

    keyword = str(args.get("keyword") or "").strip()
    status = normalize_status(args.get("status"))
    priority = normalize_priority(args.get("priority")) if args.get("priority") else None
    limit = max(1, min(int(args.get("limit") or 5), 10))

    q = db.query(Ticket)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(Ticket.title.like(like), Ticket.description.like(like), Ticket.ticket_no.like(like)))
    if status:
        q = q.filter(Ticket.status == status)
    if priority:
        q = q.filter(Ticket.priority == priority)

    rows = q.order_by(Ticket.created_at.desc()).limit(limit).all()
    return {"ok": True, "items": [_ticket_to_dict(t) for t in rows], "count": len(rows)}


def ticket_get(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    ticket = None
    if args.get("ticket_id") is not None:
        try:
            ticket = db.query(Ticket).filter(Ticket.id == int(args["ticket_id"])).first()
        except Exception:
            ticket = None
    elif args.get("ticket_no"):
        ticket_no = str(args["ticket_no"]).strip()
        ticket = db.query(Ticket).filter(Ticket.ticket_no == ticket_no).first()

    if not ticket:
        return {"ok": False, "error": "ticket not found"}
    if not is_operator(user) and ticket.reporter_id and int(ticket.reporter_id) != int(user.id):
        return {"ok": False, "error": "permission denied"}
    return {"ok": True, "ticket": _ticket_to_dict(ticket)}


def ticket_create(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    title = str(args.get("title") or "").strip()[:200]
    description = str(args.get("description") or title).strip()
    priority = normalize_priority(args.get("priority"))
    if not title:
        return {"ok": False, "error": "title is required"}

    ticket = Ticket(
        ticket_no=_generate_ticket_no(db),
        title=title,
        description=description or title,
        source="ai_auto",
        status="pending",
        priority=priority,
        reporter_id=user.id,
        reporter_name=user.username,
    )
    db.add(ticket)
    db.flush()
    db.add(
        TicketLog(
            ticket_id=ticket.id,
            action="created",
            operator_id=user.id,
            operator_name=user.username,
            content=f"Agent auto-created ticket: {title}",
        )
    )
    db.commit()
    db.refresh(ticket)
    return {"ok": True, "ticket": _ticket_to_dict(ticket)}


def analytics_summary(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    if not is_operator(user):
        return {"ok": False, "error": "permission denied"}

    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    overdue_threshold = now - timedelta(hours=48)

    data = {
        "daily_qa": db.query(func.count(Ticket.id))
        .filter(Ticket.source == "ai_auto", Ticket.created_at >= today_start)
        .scalar()
        or 0,
        "pending_tickets": db.query(func.count(Ticket.id)).filter(Ticket.status == "pending").scalar() or 0,
        "overdue_count": db.query(func.count(Ticket.id))
        .filter(Ticket.status == "pending", Ticket.created_at <= overdue_threshold)
        .scalar()
        or 0,
        "total_accounts": db.query(func.count(Account.id)).scalar() or 0,
        "new_accounts_month": db.query(func.count(Account.id)).filter(Account.created_at >= month_start).scalar()
        or 0,
        "kb_entries": db.query(func.count(KBEntry.id)).scalar() or 0,
        "kb_new_week": db.query(func.count(KBEntry.id)).filter(KBEntry.created_at >= week_ago).scalar() or 0,
    }
    return {"ok": True, "summary": data}


def system_health_check(db: Session, user: CurrentUser, args: dict[str, Any]) -> dict[str, Any]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"error: {exc}"

    try:
        vector_docs = collection_count()
        vector_status = "ok" if vector_docs >= 0 else "error"
    except Exception as exc:
        vector_status = f"error: {exc}"
        vector_docs = -1

    return {
        "ok": db_status == "connected" and vector_status == "ok",
        "database": db_status,
        "vector_store": vector_status,
        "vector_docs": vector_docs,
    }


TOOL_REGISTRY = {
    "kb_search": kb_search,
    "ticket_search": ticket_search,
    "ticket_get": ticket_get,
    "ticket_create": ticket_create,
    "analytics_summary": analytics_summary,
    "system_health_check": system_health_check,
}


def execute_tool(db: Session, user: CurrentUser, tool_name: str, args: dict[str, Any]) -> dict[str, Any]:
    started = time.perf_counter()
    fn = TOOL_REGISTRY.get(tool_name)
    if fn is None:
        result = {"ok": False, "error": f"unknown tool: {tool_name}"}
    else:
        try:
            result = fn(db, user, args or {})
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
    result["latency_ms"] = int((time.perf_counter() - started) * 1000)
    return result

