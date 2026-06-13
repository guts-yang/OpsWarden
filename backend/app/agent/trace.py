from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import engine

logger = logging.getLogger(__name__)


def init_agent_tables() -> None:
    statements = [
        """
        CREATE TABLE IF NOT EXISTS agent_runs (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            thread_id VARCHAR(160) NOT NULL,
            user_id BIGINT,
            query TEXT NOT NULL,
            final_answer TEXT,
            stop_reason VARCHAR(64),
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_agent_runs_thread_id ON agent_runs(thread_id)",
        "CREATE INDEX IF NOT EXISTS idx_agent_runs_user_id ON agent_runs(user_id)",
        """
        CREATE TABLE IF NOT EXISTS agent_tool_calls (
            id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            run_id BIGINT REFERENCES agent_runs(id) ON DELETE CASCADE,
            tool_name VARCHAR(64) NOT NULL,
            args_json JSONB,
            result_json JSONB,
            latency_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS idx_agent_tool_calls_run_id ON agent_tool_calls(run_id)",
    ]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def create_run(db: Session, thread_id: str, user_id: int, query: str) -> int | None:
    try:
        row = db.execute(
            text(
                """
                INSERT INTO agent_runs(thread_id, user_id, query)
                VALUES (:thread_id, :user_id, :query)
                RETURNING id
                """
            ),
            {"thread_id": thread_id, "user_id": user_id, "query": query},
        ).first()
        db.commit()
        return int(row[0]) if row else None
    except Exception as exc:
        db.rollback()
        logger.warning("create agent run failed: %s", exc)
        return None


def update_run(db: Session, run_id: int | None, answer: str, stop_reason: str) -> None:
    if not run_id:
        return
    try:
        db.execute(
            text("UPDATE agent_runs SET final_answer = :answer, stop_reason = :stop_reason WHERE id = :id"),
            {"id": run_id, "answer": answer, "stop_reason": stop_reason},
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("update agent run failed: %s", exc)


def record_tool_call(
    db: Session,
    run_id: int | None,
    tool_name: str,
    args: dict[str, Any],
    result: dict[str, Any],
) -> None:
    if not run_id:
        return
    try:
        db.execute(
            text(
                """
                INSERT INTO agent_tool_calls(run_id, tool_name, args_json, result_json, latency_ms, success)
                VALUES (:run_id, :tool_name, CAST(:args_json AS JSONB), CAST(:result_json AS JSONB), :latency_ms, :success)
                """
            ),
            {
                "run_id": run_id,
                "tool_name": tool_name,
                "args_json": json.dumps(args or {}, ensure_ascii=False),
                "result_json": json.dumps(result or {}, ensure_ascii=False, default=str),
                "latency_ms": int(result.get("latency_ms") or 0),
                "success": bool(result.get("ok")),
            },
        )
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning("record agent tool call failed: %s", exc)
