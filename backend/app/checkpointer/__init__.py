"""LangGraph 兼容的 PostgreSQL 状态持久化（Checkpointer）。

与 LangGraph / LangChain 文档中的 checkpoint 语义一致（参见 langchain-doc.cn）：

- **快照**：图在节点提交后由 LangGraph 调用 ``put`` 写入当前 checkpoint；
- **thread_id**：``config_helpers.thread_config`` 中配置，不同线程互不读写；
- **恢复**：下次对同一 ``thread_id`` ``invoke`` 时自动加载最新 checkpoint；
- **时间旅行**：``time_travel_config(thread_id, checkpoint_id)`` 后 ``invoke``，从该快照继续。

典型用法::

    from app.checkpointer import get_postgres_saver, thread_config, time_travel_config

    saver = get_postgres_saver()
    graph.compile(checkpointer=saver).invoke(state, config=thread_config("session-1"))
"""

from app.checkpointer.config_helpers import thread_config, time_travel_config
from app.checkpointer.runtime import (
    close_checkpointer_pool,
    get_postgres_saver,
    init_checkpointer_pool,
    list_checkpoint_summaries,
)

__all__ = [
    "thread_config",
    "time_travel_config",
    "get_postgres_saver",
    "init_checkpointer_pool",
    "close_checkpointer_pool",
    "list_checkpoint_summaries",
]
