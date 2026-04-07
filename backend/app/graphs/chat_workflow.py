"""AI 问答 LangGraph：每轮写入 checkpoint，按 thread_id 隔离并累积 history。"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres import PostgresSaver
from sqlalchemy.orm import Session

from app.checkpointer import get_postgres_saver
from app.middleware.auth import CurrentUser
from app.rag.chat_pipeline import run_chat_pipeline


class ChatGraphState(TypedDict, total=False):
    """持久化到 checkpoint 的通道（勿放入 db / user 等非序列化对象）。"""

    query: str
    history: Annotated[list[dict[str, Any]], operator.add]
    answer: str
    source: str
    kb_entry_id: int | None
    question: str | None
    category: str | None
    ticket_no: str | None
    ticket_id: int | None


async def _chat_node(state: ChatGraphState, config: RunnableConfig) -> dict[str, Any]:
    db: Session = config["configurable"]["db"]
    user: CurrentUser = config["configurable"]["user"]
    q = (state.get("query") or "").strip()
    if not q:
        return {
            "answer": "请输入您的问题。",
            "source": "fallback",
            "history": [],
        }

    result = await run_chat_pipeline(db, user, q)
    turn = [
        {"role": "user", "content": q},
        {
            "role": "assistant",
            "content": result.get("answer", ""),
            "source": result.get("source"),
            "ticket_no": result.get("ticket_no"),
            "ticket_id": result.get("ticket_id"),
            "kb_entry_id": result.get("kb_entry_id"),
        },
    ]
    out: dict[str, Any] = {
        "answer": result.get("answer", ""),
        "source": result.get("source", "fallback"),
        "history": turn,
    }
    for key in ("kb_entry_id", "question", "category", "ticket_no", "ticket_id"):
        if key in result:
            out[key] = result[key]
    return out


def build_chat_graph(checkpointer: PostgresSaver):
    g = StateGraph(ChatGraphState)
    g.add_node("chat", _chat_node)
    g.add_edge(START, "chat")
    g.add_edge("chat", END)
    return g.compile(checkpointer=checkpointer)


_compiled_chat_graph = None
_compiled_for_saver_id: int | None = None


def get_compiled_chat_graph():
    """在 checkpointer 可用时编译并缓存；Saver 实例变化时重新 compile。"""
    global _compiled_chat_graph, _compiled_for_saver_id
    saver = get_postgres_saver()
    if saver is None:
        _compiled_chat_graph = None
        _compiled_for_saver_id = None
        return None
    sid = id(saver)
    if _compiled_chat_graph is None or _compiled_for_saver_id != sid:
        _compiled_chat_graph = build_chat_graph(saver)
        _compiled_for_saver_id = sid
    return _compiled_chat_graph


async def invoke_chat_with_checkpoint(
    *,
    db: Session,
    user: CurrentUser,
    thread_id: str,
    query: str,
) -> ChatGraphState:
    graph = get_compiled_chat_graph()
    if graph is None:
        raise RuntimeError("checkpointer unavailable")
    cfg: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "db": db,
            "user": user,
        }
    }
    return await graph.ainvoke({"query": query}, config=cfg)  # type: ignore[return-value]
