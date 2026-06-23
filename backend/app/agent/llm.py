from __future__ import annotations

import json
import logging
import re
from typing import Any

import httpx

from app.agent.prompts import AGENT_SYSTEM_PROMPT, AVAILABLE_TOOLS
from app.config import get_settings

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r"\{.*\}", text, flags=re.S)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def heuristic_decision(query: str, observations: list[dict[str, Any]], step_count: int) -> dict[str, Any]:
    q = (query or "").strip()
    q_lower = q.lower()

    greeting_words = {"hi", "hello", "hey", "你好", "您好"}
    if not observations and q_lower in greeting_words:
        return {
            "type": "final_answer",
            "answer": "你好，我是 OpsWarden 运维助手。你可以直接描述故障现象、查询工单状态，或让我帮你检索知识库。",
            "confidence": 0.9,
        }

    if observations:
        last = observations[-1]
        tool = last.get("tool")
        result = last.get("result") or {}
        if tool == "kb_search" and result.get("items"):
            items = result["items"]
            first = items[0]
            return {
                "type": "final_answer",
                "answer": first.get("solution") or "已找到匹配的知识库内容。",
                "confidence": float(first.get("score") or 0.7),
            }
        if tool == "kb_search":
            return {
                "type": "confirm_action",
                "answer": (
                    "我没有在知识库中检索到可直接召回的解决方案。"
                    "可以先根据通用运维经验继续分析：请优先补充故障现象、影响范围、发生时间、错误日志或截图。"
                    "如果这是需要运维人员跟进的问题，我可以为你创建一张工单。是否需要创建？"
                ),
                "confidence": 0.55,
                "pending_action": {
                    "type": "tool_call",
                    "tool": "ticket_create",
                    "args": {"title": q[:120], "description": q, "priority": "medium"},
                },
            }
        if tool == "ticket_search":
            items = result.get("items") or []
            if items:
                lines = [
                    f"{x['ticket_no']} [{x['status']}/{x['priority']}]: {x['title']}"
                    for x in items[:5]
                ]
                return {
                    "type": "final_answer",
                    "answer": "找到相关工单：\n" + "\n".join(lines),
                    "confidence": 0.8,
                }
        if tool == "ticket_get" and result.get("ticket"):
            t = result["ticket"]
            return {
                "type": "final_answer",
                "answer": (
                    f"工单 {t['ticket_no']} 当前状态为 {t['status']}，优先级 {t['priority']}。"
                    f"标题：{t['title']}"
                ),
                "confidence": 0.8,
            }
        if tool == "ticket_create" and result.get("ticket"):
            t = result["ticket"]
            return {
                "type": "final_answer",
                "answer": f"已为你创建工单 {t['ticket_no']}，当前状态为 {t['status']}，运维人员会继续跟进。",
                "confidence": 0.9,
            }
        if tool == "analytics_summary" and result.get("summary"):
            s = result["summary"]
            return {
                "type": "final_answer",
                "answer": (
                    f"今日 AI 创建工单 {s['daily_qa']} 个，待处理 {s['pending_tickets']} 个，"
                    f"逾期 {s['overdue_count']} 个，知识库条目 {s['kb_entries']} 条。"
                ),
                "confidence": 0.8,
            }
        if tool == "system_health_check":
            return {
                "type": "final_answer",
                "answer": (
                    f"数据库状态：{result.get('database')}；向量库状态：{result.get('vector_store')}；"
                    f"可检索知识条目：{result.get('vector_docs')}。"
                ),
                "confidence": 0.8,
            }
        if step_count >= 2:
            return {
                "type": "ask_user",
                "answer": "我还没有找到足够匹配的信息。请补充受影响系统、发生时间和具体错误信息。",
                "confidence": 0.4,
            }

    ticket_words = ["ticket", "work order", "工单", "报修", "建单", "创建"]
    status_words = ["status", "状态", "进度", "处理了吗", "编号"]
    analytics_words = ["统计", "仪表盘", "dashboard", "数量", "逾期", "待处理"]
    health_words = ["健康", "health", "状态检查", "系统状态", "向量库", "数据库"]

    if any(w in q_lower for w in analytics_words):
        return {"type": "tool_call", "tool": "analytics_summary", "args": {}, "confidence": 0.7}
    if any(w in q_lower for w in health_words):
        return {"type": "tool_call", "tool": "system_health_check", "args": {}, "confidence": 0.7}
    if any(w in q_lower for w in ticket_words) and any(w in q_lower for w in status_words):
        return {"type": "tool_call", "tool": "ticket_search", "args": {"keyword": q, "limit": 5}, "confidence": 0.7}
    if any(w in q_lower for w in ticket_words):
        return {
            "type": "tool_call",
            "tool": "ticket_create",
            "args": {"title": q[:120], "description": q, "priority": "medium"},
            "confidence": 0.6,
        }
    return {"type": "tool_call", "tool": "kb_search", "args": {"query": q, "top_k": 3}, "confidence": 0.6}


async def decide_with_llm(
    *,
    query: str,
    history: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    user_role: str,
    step_count: int,
) -> dict[str, Any]:
    settings = get_settings()
    if not settings.OLLAMA_BASE_URL:
        return heuristic_decision(query, observations, step_count)

    payload = {
        "query": query,
        "user_role": user_role,
        "step_count": step_count,
        "available_tools": AVAILABLE_TOOLS,
        "recent_history": history[-8:],
        "observations": observations[-5:],
    }
    messages = [
        {"role": "system", "content": AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]

    try:
        async with httpx.AsyncClient(timeout=settings.OLLAMA_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.OLLAMA_BASE_URL}/v1/chat/completions",
                json={
                    "model": settings.OLLAMA_MODEL,
                    "messages": messages,
                    "temperature": 0.0,
                    "max_tokens": 700,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        logger.warning("Agent LLM decision failed: %s", exc)
        return heuristic_decision(query, observations, step_count)

    parsed = _extract_json(content or "")
    if not parsed:
        logger.warning("Agent LLM returned non-json decision: %s", content)
        return heuristic_decision(query, observations, step_count)
    return parsed
