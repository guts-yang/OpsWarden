"""最小两节点图：验证节点级 checkpoint 写入与 thread 隔离。

用法：在 REPL 或测试中 ``run_demo("thread-1")``；时间旅行可先 ``list_checkpoint_summaries`` 取 id 再
``run_demo("thread-1", checkpoint_id=...)``。
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.postgres import PostgresSaver

from app.checkpointer import get_postgres_saver, thread_config, time_travel_config


class DemoState(TypedDict):
    step: int
    last_node: str


def _node_a(state: DemoState) -> dict:
    return {"step": state["step"] + 1, "last_node": "a"}


def _node_b(state: DemoState) -> dict:
    return {"step": state["step"] + 1, "last_node": "b"}


def build_demo_graph(checkpointer: PostgresSaver):
    g = StateGraph(DemoState)
    g.add_node("a", _node_a)
    g.add_node("b", _node_b)
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    return g.compile(checkpointer=checkpointer)


def run_demo(thread_id: str, checkpoint_id: str | None = None) -> DemoState:
    saver = get_postgres_saver()
    if saver is None:
        raise RuntimeError("Checkpointer 未初始化，请确认数据库可用且应用 startup 已成功执行 init_checkpointer_pool")
    app = build_demo_graph(saver)
    if checkpoint_id:
        cfg = time_travel_config(thread_id, checkpoint_id)
        # ``None``：不覆盖 channel，仅从该 checkpoint 恢复后再向下执行（时间旅行）
        result = app.invoke(None, config=cfg)
    else:
        cfg = thread_config(thread_id)
        result = app.invoke({"step": 0, "last_node": ""}, config=cfg)
    return result  # type: ignore[return-value]
