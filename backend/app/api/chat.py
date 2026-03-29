from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.models.ticket import Ticket, TicketLog
from app.middleware.auth import get_current_user, CurrentUser
from app.utils.response import success
from app.rag.retriever import search as rag_search
from app.rag.llm import generate_answer

router = APIRouter(prefix="/api/chat", tags=["AI问答"])


class ChatRequest(BaseModel):
    query: str


def _generate_ticket_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"T-{today}-"
    last = db.query(Ticket).filter(Ticket.ticket_no.like(f"{prefix}%")).order_by(Ticket.ticket_no.desc()).first()
    num = (int(last.ticket_no.split("-")[-1]) + 1) if last else 1
    return f"{prefix}{num:03d}"


@router.post("", summary="AI问答（RAG语义检索 + DeepSeek生成 + 工单兜底）")
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = req.query.strip()
    if not query:
        return success(data={"answer": "请输入您的问题。", "source": "fallback"})

    # 1. Semantic search in ChromaDB
    results = rag_search(query)

    if results:
        # 2. Use DeepSeek to generate a contextual answer; fall back to raw solution if LLM unavailable
        answer = await generate_answer(query, results) or results[0]["solution"]
        return success(data={
            "answer":      answer,
            "source":      "kb",
            "kb_entry_id": results[0]["id"],
            "question":    results[0]["question"],
            "category":    results[0]["category"],
        })

    # 3. No KB match — auto-create ticket
    ticket = Ticket(
        ticket_no=_generate_ticket_no(db),
        title=query[:200],
        description=query,
        source="ai_auto",
        status="pending",
        priority="medium",
        reporter_id=current_user.id,
        reporter_name=current_user.username,
    )
    db.add(ticket)
    db.flush()
    db.add(TicketLog(
        ticket_id=ticket.id,
        action="created",
        operator_id=current_user.id,
        operator_name=current_user.username,
        content=f"AI问答未命中知识库，自动生成工单：{query[:100]}",
    ))
    db.commit()
    db.refresh(ticket)

    return success(data={
        "answer":    f"抱歉，我暂时无法直接解答该问题。已为您自动创建工单 {ticket.ticket_no}，运维人员将尽快处理。",
        "source":    "fallback",
        "ticket_no": ticket.ticket_no,
        "ticket_id": ticket.id,
    })
