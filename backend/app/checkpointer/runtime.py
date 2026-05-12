"""PostgreSQL 连接池 + LangGraph ``PostgresSaver`` 单例生命周期。"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.checkpointer.config_helpers import thread_config
from app.checkpointer.conninfo import sqlalchemy_url_to_psycopg_conninfo
from app.config import get_settings

logger = logging.getLogger(__name__)

_pool: ConnectionPool | None = None
_saver: PostgresSaver | None = None


def init_checkpointer_pool() -> None:
    """创建连接池、``PostgresSaver``，并执行 ``setup()``（建表 / 迁移）。"""
    global _pool, _saver
    close_checkpointer_pool()
    settings = get_settings()
    conninfo = sqlalchemy_url_to_psycopg_conninfo(settings.DATABASE_URL)
    pool = ConnectionPool(
        conninfo=conninfo,
        max_size=20,
        kwargs={
            "autocommit": True,
            "prepare_threshold": 0,
            "row_factory": dict_row,
        },
    )
    try:
        saver = PostgresSaver(pool)
        saver.setup()
    except Exception:
        pool.close()
        raise
    _pool = pool
    _saver = saver
    logger.info("LangGraph PostgresSaver 已初始化（checkpoint 表就绪）")


def close_checkpointer_pool() -> None:
    global _pool, _saver
    if _pool is not None:
        try:
            _pool.close()
        except Exception as e:
            logger.warning("关闭 checkpointer 连接池时出错：%s", e)
    _pool = None
    _saver = None


def get_postgres_saver() -> PostgresSaver | None:
    return _saver


def list_checkpoint_summaries(thread_id: str, limit: int = 20) -> list[dict[str, Any]]:
    """列出某线程下最近若干 checkpoint（新→旧），供调试或时间旅行选点。"""
    saver = get_postgres_saver()
    if saver is None:
        return []
    cfg = thread_config(thread_id)
    rows: list[dict[str, Any]] = []
    for tup in saver.list(cfg, limit=limit):
        cid = tup.config["configurable"].get("checkpoint_id")
        rows.append({"checkpoint_id": cid, "metadata": tup.metadata})
    return rows
