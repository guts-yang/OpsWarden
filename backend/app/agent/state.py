from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict


class AgentState(TypedDict, total=False):
    query: str
    user_id: int
    username: str
    role: str
    run_id: int | None

    history: Annotated[list[dict[str, Any]], operator.add]
    memory_summary: str

    action: dict[str, Any]
    answer: str
    source: str
    confidence: float

    kb_refs: list[dict[str, Any]]
    ticket_no: str | None
    ticket_id: int | None

    tool_calls: Annotated[list[dict[str, Any]], operator.add]
    observations: Annotated[list[dict[str, Any]], operator.add]

    needs_confirmation: bool
    pending_action: dict[str, Any] | None

    step_count: int
    stop_reason: str
