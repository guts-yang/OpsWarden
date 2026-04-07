"""单次 AI 问答管线（RAG + 工单兜底），供 HTTP 与 LangGraph 节点复用。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.middleware.auth import CurrentUser
from app.models.ticket import Ticket, TicketLog
from app.rag.llm import generate_answer
from app.rag.retriever import search as rag_search


def generate_ticket_no(db: Session) -> str:
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


async def run_chat_pipeline(db: Session, user: CurrentUser, query: str) -> dict:
    """
    执行一轮问答，返回与原先 /api/chat 一致的 data 字段（不含信封）。
    """
    q = query.strip()
    if not q:
        return {"answer": "请输入您的问题。", "source": "fallback"}

    results = rag_search(q)
    if results:
        answer = await generate_answer(q, results) or results[0]["solution"]
        return {
            "answer": answer,
            "source": "kb",
            "kb_entry_id": results[0]["id"],
            "question": results[0]["question"],
            "category": results[0]["category"],
        }

    ticket = Ticket(
        ticket_no=generate_ticket_no(db),
        title=q[:200],
        description=q,
        source="ai_auto",
        status="pending",
        priority="medium",
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
            content=f"AI问答未命中知识库，自动生成工单：{q[:100]}",
        )
    )
    db.commit()
    db.refresh(ticket)

    return {
        "answer": (
            f"抱歉，我暂时无法直接解答该问题。已为您自动创建工单 {ticket.ticket_no}，"
            "运维人员将尽快处理。"
        ),
        "source": "fallback",
        "ticket_no": ticket.ticket_no,
        "ticket_id": ticket.id,
    }
