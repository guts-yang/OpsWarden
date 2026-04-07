"""LangGraph RunnableConfig 构造：thread 隔离与时间旅行。"""

from langchain_core.runnables import RunnableConfig


def thread_config(thread_id: str, checkpoint_ns: str = "") -> RunnableConfig:
    """新对话或继续当前线程最新状态：仅指定 ``thread_id``。"""
    return {
        "configurable": {
            "thread_id": str(thread_id),
            "checkpoint_ns": checkpoint_ns,
        }
    }


def time_travel_config(
    thread_id: str, checkpoint_id: str, checkpoint_ns: str = ""
) -> RunnableConfig:
    """从某历史 checkpoint 恢复（时间旅行），再 ``invoke`` 即在该快照基础上继续。"""
    return {
        "configurable": {
            "thread_id": str(thread_id),
            "checkpoint_ns": checkpoint_ns,
            "checkpoint_id": str(checkpoint_id),
        }
    }
