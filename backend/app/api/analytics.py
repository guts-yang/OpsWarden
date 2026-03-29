from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from datetime import datetime

from app.database import get_db
from app.models.ticket import Ticket
from app.models.account import Account
from app.middleware.auth import get_current_user, CurrentUser
from app.utils.response import success

router = APIRouter(prefix="/api/analytics", tags=["数据分析"])


@router.get("/summary", summary="汇总统计：工单量、平均响应时间、解决率")
def get_summary(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    total = db.query(func.count(Ticket.id)).scalar() or 0

    resolved_count = (
        db.query(func.count(Ticket.id))
        .filter(Ticket.status.in_(["resolved", "closed"]))
        .scalar()
        or 0
    )

    resolution_rate = round(resolved_count / total * 100, 1) if total > 0 else 0.0

    # 平均响应时间（秒），仅统计已有 resolved_at 的工单
    avg_seconds = (
        db.query(
            func.avg(
                func.timestampdiff(
                    func.literal_column("SECOND"),
                    Ticket.created_at,
                    Ticket.resolved_at,
                )
            )
        )
        .filter(Ticket.resolved_at.isnot(None))
        .scalar()
    )

    if avg_seconds:
        mins = int(avg_seconds // 60)
        secs = int(avg_seconds % 60)
        avg_response_time = f"{mins}m {secs:02d}s"
    else:
        avg_response_time = "—"

    # 各状态分布
    status_rows = (
        db.query(Ticket.status, func.count(Ticket.id))
        .group_by(Ticket.status)
        .all()
    )
    status_dist = {row[0]: row[1] for row in status_rows}

    return success(
        data={
            "total_tickets": total,
            "resolved_count": resolved_count,
            "resolution_rate": resolution_rate,
            "avg_response_time": avg_response_time,
            "status_distribution": status_dist,
        }
    )


@router.get("/operators", summary="运维员绩效排行榜")
def get_operators(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    # 统计每位运维员解决的工单数量及平均响应时间
    rows = (
        db.query(
            Account.id,
            Account.name,
            Account.department,
            func.count(Ticket.id).label("resolved_count"),
            func.avg(
                func.timestampdiff(
                    func.literal_column("SECOND"),
                    Ticket.created_at,
                    Ticket.resolved_at,
                )
            ).label("avg_seconds"),
        )
        .join(Ticket, Ticket.assignee_id == Account.id, isouter=True)
        .filter(Ticket.status.in_(["resolved", "closed"]))
        .group_by(Account.id, Account.name, Account.department)
        .order_by(func.count(Ticket.id).desc())
        .limit(10)
        .all()
    )

    leaderboard = []
    for rank, row in enumerate(rows, start=1):
        avg_s = row.avg_seconds or 0
        mins = int(avg_s // 60)
        secs = int(avg_s % 60)
        leaderboard.append(
            {
                "rank": rank,
                "id": row.id,
                "name": row.name,
                "department": row.department,
                "resolved_count": row.resolved_count,
                "avg_response_time": f"{mins}m {secs:02d}s" if avg_s else "—",
            }
        )

    return success(data=leaderboard)
