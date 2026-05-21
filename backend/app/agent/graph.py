from __future__ import annotations

from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.agent.llm import decide_with_llm
from app.agent.policy import requires_confirmation, tool_allowed
from app.agent.state import AgentState
from app.agent.tools import execute_tool
from app.checkpointer import get_postgres_saver
from app.middleware.auth import CurrentUser
from app.rag.llm import generate_general_answer

MAX_AGENT_STEPS = 5

CONFIRM_WORDS = {"确认", "同意", "执行", "继续", "yes", "y", "ok", "confirm"}
CANCEL_WORDS = {"取消", "暂不", "不用", "不要", "否", "no", "n", "cancel"}


def _latest_turn_observations(state: AgentState) -> list[dict[str, Any]]:
    run_id = state.get("run_id")
    query = state.get("query")
    observations = state.get("observations") or []
    if run_id is not None:
        return [obs for obs in observations if obs.get("run_id") == run_id][-5:]
    if not query:
        return observations[-5:]
    out: list[dict[str, Any]] = []
    for obs in reversed(observations):
        if obs.get("query") != query:
            break
        out.append(obs)
    return list(reversed(out))


async def _load_context_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    user: CurrentUser = config["configurable"]["user"]
    run_id = config["configurable"].get("agent_run_id")
    return {
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
        "run_id": run_id,
        "step_count": 0,
        "action": {},
        "answer": "",
        "source": "agent",
        "confidence": 0.0,
        "kb_refs": [],
        "ticket_no": None,
        "ticket_id": None,
        "stop_reason": "",
    }


async def _decide_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    q = (state.get("query") or "").strip()
    q_lower = q.lower()
    pending_action = state.get("pending_action")
    if state.get("needs_confirmation") and pending_action:
        if any(word in q_lower for word in CONFIRM_WORDS) and pending_action.get("type") == "tool_call":
            action = dict(pending_action)
            action["confirmed"] = True
            return {
                "action": action,
                "needs_confirmation": False,
                "pending_action": None,
                "answer": "",
                "stop_reason": "",
            }
        if any(word in q_lower for word in CANCEL_WORDS):
            return {
                "action": {"type": "final_answer"},
                "answer": "已取消待确认操作。",
                "source": "agent",
                "confidence": 1.0,
                "needs_confirmation": False,
                "pending_action": None,
                "stop_reason": "cancelled",
            }
        return {
            "action": {"type": "final_answer"},
            "answer": state.get("answer") or "该操作需要确认后才能继续。",
            "source": "agent",
            "confidence": state.get("confidence") or 0.7,
            "stop_reason": "needs_confirmation",
        }

    if not q:
        return {
            "action": {"type": "final_answer"},
            "answer": "请输入您的问题。",
            "source": "fallback",
            "confidence": 1.0,
            "stop_reason": "empty_query",
        }

    step_count = int(state.get("step_count") or 0)
    if step_count >= MAX_AGENT_STEPS:
        return {
            "action": {"type": "final_answer"},
            "answer": "我已经完成当前可用的信息收集，但需要更多细节才能继续安全处理。",
            "source": "agent",
            "confidence": 0.4,
            "stop_reason": "step_limit",
        }

    turn_observations = _latest_turn_observations(state)
    if turn_observations:
        last = turn_observations[-1]
        result = last.get("result") or {}
        if last.get("tool") == "kb_search" and not result.get("items"):
            general = await generate_general_answer(q)
            answer = general or (
                "我没有在知识库中检索到可直接召回的解决方案。"
                "可以先根据通用运维经验继续分析：请补充故障现象、影响范围、发生时间、错误日志或截图。"
            )
            return {
                "action": {"type": "confirm_action"},
                "answer": f"{answer}\n\n是否需要我为你创建工单？",
                "source": "agent",
                "confidence": 0.6,
                "needs_confirmation": True,
                "pending_action": {
                    "type": "tool_call",
                    "tool": "ticket_create",
                    "args": {"title": q[:120], "description": q, "priority": "medium"},
                },
                "stop_reason": "needs_confirmation",
            }

    decision = await decide_with_llm(
        query=q,
        history=state.get("history") or [],
        observations=turn_observations,
        user_role=str(state.get("role") or ""),
        step_count=step_count,
    )
    action_type = decision.get("type") or "final_answer"
    if action_type in {"final_answer", "ask_user"}:
        return {
            "action": decision,
            "answer": str(decision.get("answer") or ""),
            "source": "kb" if state.get("kb_refs") else "agent",
            "confidence": float(decision.get("confidence") or 0.6),
            "stop_reason": action_type,
        }
    if action_type == "confirm_action":
        return {
            "action": decision,
            "answer": str(decision.get("answer") or "该操作需要您确认后才能继续。"),
            "source": "agent",
            "confidence": float(decision.get("confidence") or 0.6),
            "needs_confirmation": True,
            "pending_action": decision.get("pending_action") or {},
            "stop_reason": "needs_confirmation",
        }
    return {"action": decision}


def _route_after_decide(state: AgentState) -> str:
    action = state.get("action") or {}
    if action.get("type") == "tool_call":
        return "tool"
    return "final"


async def _tool_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    db: Session = config["configurable"]["db"]
    user: CurrentUser = config["configurable"]["user"]
    run_id = config["configurable"].get("agent_run_id")
    record_tool_call = config["configurable"].get("record_tool_call")

    action = state.get("action") or {}
    tool_name = str(action.get("tool") or "")
    args = action.get("args") or {}
    if not isinstance(args, dict):
        args = {}

    if not tool_allowed(tool_name, user):
        result = {"ok": False, "error": "permission denied", "latency_ms": 0}
    elif requires_confirmation(tool_name, args, user) and not action.get("confirmed"):
        return {
            "answer": (
                "我可以为你创建工单，但不会自动提交。"
                "请确认是否创建；确认后我会调用工单工具完成创建。"
            ),
            "source": "agent",
            "confidence": 0.7,
            "needs_confirmation": True,
            "pending_action": {"type": "tool_call", "tool": tool_name, "args": args},
            "stop_reason": "needs_confirmation",
            "action": {"type": "final_answer"},
        }
    else:
        result = execute_tool(db, user, tool_name, args)

    if record_tool_call:
        record_tool_call(db, run_id, tool_name, args, result)

    obs = {
        "run_id": state.get("run_id"),
        "query": state.get("query"),
        "tool": tool_name,
        "args": args,
        "result": result,
    }
    updates: dict[str, Any] = {
        "observations": [obs],
        "tool_calls": [
            {
                "run_id": state.get("run_id"),
                "query": state.get("query"),
                "tool": tool_name,
                "args": args,
                "ok": bool(result.get("ok")),
            }
        ],
        "step_count": int(state.get("step_count") or 0) + 1,
    }

    if tool_name == "kb_search" and result.get("items"):
        updates["kb_refs"] = [
            {
                "id": item.get("id"),
                "question": item.get("question"),
                "category": item.get("category"),
                "score": item.get("score"),
            }
            for item in result.get("items", [])
        ]
    if tool_name in {"ticket_create", "ticket_get"} and result.get("ticket"):
        ticket = result["ticket"]
        updates["ticket_no"] = ticket.get("ticket_no")
        updates["ticket_id"] = ticket.get("id")
    return updates


async def _final_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    q = (state.get("query") or "").strip()
    answer = state.get("answer") or "我需要更多细节才能继续处理。"
    turn = [
        {"role": "user", "content": q},
        {
            "role": "assistant",
            "content": answer,
            "source": state.get("source") or "agent",
            "ticket_no": state.get("ticket_no"),
            "ticket_id": state.get("ticket_id"),
            "kb_refs": state.get("kb_refs") or [],
        },
    ]
    return {"history": turn}


def build_agent_graph(checkpointer: PostgresSaver):
    g = StateGraph(AgentState)
    g.add_node("load_context", _load_context_node)
    g.add_node("decide", _decide_node)
    g.add_node("tool", _tool_node)
    g.add_node("final", _final_node)
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "decide")
    g.add_conditional_edges("decide", _route_after_decide, {"tool": "tool", "final": "final"})
    g.add_edge("tool", "decide")
    g.add_edge("final", END)
    return g.compile(checkpointer=checkpointer)


_compiled_agent_graph = None
_compiled_for_saver_id: int | None = None


def get_compiled_agent_graph():
    global _compiled_agent_graph, _compiled_for_saver_id
    saver = get_postgres_saver()
    if saver is None:
        _compiled_agent_graph = None
        _compiled_for_saver_id = None
        return None
    sid = id(saver)
    if _compiled_agent_graph is None or _compiled_for_saver_id != sid:
        _compiled_agent_graph = build_agent_graph(saver)
        _compiled_for_saver_id = sid
    return _compiled_agent_graph


async def invoke_agent_with_checkpoint(
    *,
    db: Session,
    user: CurrentUser,
    thread_id: str,
    query: str,
    agent_run_id: int | None = None,
) -> AgentState:
    graph = get_compiled_agent_graph()
    if graph is None:
        raise RuntimeError("checkpointer unavailable")
    cfg: RunnableConfig = {
        "configurable": {
            "thread_id": thread_id,
            "checkpoint_ns": "",
            "db": db,
            "user": user,
            "agent_run_id": agent_run_id,
        }
    }
    from app.agent.trace import record_tool_call

    cfg["configurable"]["record_tool_call"] = record_tool_call
    return await graph.ainvoke({"query": query}, config=cfg)  # type: ignore[return-value]
