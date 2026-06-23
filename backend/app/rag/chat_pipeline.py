"""Single-turn fallback chat pipeline used when the Agent graph is unavailable."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.middleware.auth import CurrentUser
from app.models.ticket import Ticket
from app.rag.llm import generate_answer, generate_general_answer
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
    """Run one safe fallback turn.

    Important: this fallback must not auto-create tickets. Ticket creation is an
    Agent tool action and requires explicit user confirmation.
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
            "score": results[0]["score"],  # 添加分数
            "top_3_scores": [{"question": r["question"][:50], "score": r["score"]} for r in results[:3]],  # 前3条分数
        }

    general = await generate_general_answer(q)
    answer = general or (
        "我没有在知识库中检索到可直接召回的解决方案。"
        "可以先根据通用运维经验继续分析：请补充故障现象、影响范围、发生时间、错误日志或截图。"
    )
    return {
        "answer": f"{answer}\n\n是否需要我为你创建工单？",
        "source": "agent",
        "needs_confirmation": True,
        "pending_action": {
            "type": "tool_call",
            "tool": "ticket_create",
            "args": {"title": q[:120], "description": q, "priority": "medium"},
        },
    }
