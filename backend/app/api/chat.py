import re
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_user, CurrentUser
from app.utils.response import success
from app.rag.chat_pipeline import run_chat_pipeline
from app.graphs.chat_workflow import invoke_chat_with_checkpoint

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI问答"])

_THREAD_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


class ChatRequest(BaseModel):
    query: str
    thread_id: str | None = Field(
        default=None,
        description="客户端会话 ID（UUID 等），用于 checkpoint 多轮隔离；缺省为 default",
    )


def _resolve_thread_id(user: CurrentUser, raw: str | None) -> str:
    if raw is None or not isinstance(raw, str):
        return f"user-{user.id}-default"
    s = raw.strip()
    if not s or not _THREAD_ID_PATTERN.fullmatch(s):
        return f"user-{user.id}-default"
    return f"user-{user.id}-{s}"


@router.post("", summary="AI问答（RAG + DeepSeek + 工单兜底，支持 thread checkpoint）")
async def chat(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    query = req.query.strip()
    thread_id = _resolve_thread_id(current_user, req.thread_id)

    if not query:
        return success(
            data={
                "answer": "请输入您的问题。",
                "source": "fallback",
                "thread_id": thread_id,
                "checkpointed": False,
            }
        )

    graph_ok = True
    try:
        final = await invoke_chat_with_checkpoint(
            db=db,
            user=current_user,
            thread_id=thread_id,
            query=query,
        )
    except RuntimeError:
        graph_ok = False
        final = None
    except Exception as e:
        logger.warning("LangGraph 问答失败，回退无 checkpoint 模式：%s", e)
        graph_ok = False
        final = None

    if not graph_ok or final is None:
        data = await run_chat_pipeline(db, current_user, query)
        data["thread_id"] = thread_id
        data["checkpointed"] = False
        return success(data=data)

    history = final.get("history") or []
    data = {
        "answer": final.get("answer", ""),
        "source": final.get("source", "fallback"),
        "thread_id": thread_id,
        "checkpointed": True,
        "history_turns": len(history) // 2,
    }
    if final.get("source") == "kb":
        data["kb_entry_id"] = final.get("kb_entry_id")
        data["question"] = final.get("question")
        data["category"] = final.get("category")
    if final.get("ticket_no"):
        data["ticket_no"] = final.get("ticket_no")
        data["ticket_id"] = final.get("ticket_id")

    return success(data=data)
