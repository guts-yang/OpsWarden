from __future__ import annotations

from typing import Any

from app.middleware.auth import CurrentUser


OPERATOR_ROLES = {"admin", "operator"}
ALLOWED_PRIORITIES = {"low", "medium", "high", "urgent"}
ALLOWED_STATUSES = {"pending", "processing", "resolved", "closed"}


def is_operator(user: CurrentUser) -> bool:
    return user.role in OPERATOR_ROLES


def normalize_priority(value: Any) -> str:
    priority = str(value or "medium").lower()
    return priority if priority in ALLOWED_PRIORITIES else "medium"


def normalize_status(value: Any) -> str | None:
    if value is None:
        return None
    status = str(value).lower()
    return status if status in ALLOWED_STATUSES else None


def tool_allowed(tool_name: str, user: CurrentUser) -> bool:
    if tool_name in {"kb_search", "ticket_create", "ticket_get", "system_health_check"}:
        return True
    if tool_name in {"ticket_search", "analytics_summary"}:
        return is_operator(user)
    return False


def requires_confirmation(tool_name: str, args: dict[str, Any], user: CurrentUser) -> bool:
    return tool_name == "ticket_create"
