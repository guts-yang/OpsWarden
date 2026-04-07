"""按角色生成工号：前缀 + 5 位序号（与同角色下已有规范工号取 max+1）。"""
import re
from sqlalchemy.orm import Session

from app.models.account import Account

# role -> (前缀, 匹配该前缀+5位数字的正则)
_ROLE_EMPLOYEE_ID_RULES: dict[str, tuple[str, re.Pattern]] = {
    "admin": ("ADM", re.compile(r"^ADM(\d{5})$")),
    "operator": ("OPS", re.compile(r"^OPS(\d{5})$")),
    "user": ("USR", re.compile(r"^USR(\d{5})$")),
}


def allocate_employee_id(db: Session, role: str) -> str:
    if role not in _ROLE_EMPLOYEE_ID_RULES:
        raise ValueError(f"unknown role for employee_id: {role}")
    prefix, pattern = _ROLE_EMPLOYEE_ID_RULES[role]
    rows = (
        db.query(Account.employee_id)
        .filter(Account.role == role)
        .all()
    )
    max_n = 0
    for (eid,) in rows:
        if not eid:
            continue
        m = pattern.match(eid)
        if m:
            max_n = max(max_n, int(m.group(1)))
    return f"{prefix}{max_n + 1:05d}"
