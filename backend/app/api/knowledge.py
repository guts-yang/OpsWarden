from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.knowledge import KBEntry
from app.schemas.knowledge import (
    KBEntryCreate, KBEntryUpdate, KBEntryResponse,
    KBEntryListResponse, KBStatsResponse
)
from app.middleware.auth import get_current_user, CurrentUser
from app.utils.response import success
from app.rag.retriever import add_entry as chroma_add, delete_entry as chroma_delete

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/stats", summary="知识库统计数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    week_ago = datetime.now() - timedelta(days=7)
    total    = db.query(func.count(KBEntry.id)).scalar() or 0
    new_week = db.query(func.count(KBEntry.id)).filter(KBEntry.created_at >= week_ago).scalar() or 0
    writeback = db.query(func.count(KBEntry.id)).filter(KBEntry.source == "ticket_writeback").scalar() or 0
    avg_score_row = db.query(func.avg(KBEntry.match_score)).scalar()
    avg_score = round(float(avg_score_row), 2) if avg_score_row else 0.0

    return success(data=KBStatsResponse(
        total=total,
        new_this_week=new_week,
        ticket_writeback=writeback,
        avg_match_score=avg_score,
    ).model_dump())


@router.get("", summary="查询知识库列表")
def list_entries(
    category:  Optional[str] = Query(None),
    source:    Optional[str] = Query(None),
    keyword:   Optional[str] = Query(None),
    page:      int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    q = db.query(KBEntry)
    if category:
        q = q.filter(KBEntry.category == category)
    if source:
        q = q.filter(KBEntry.source == source)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(
            KBEntry.question.like(like),
            KBEntry.solution.like(like),
            KBEntry.tags.like(like),
        ))
    total = q.count()
    items = q.order_by(KBEntry.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return success(data=KBEntryListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[KBEntryResponse.model_validate(e) for e in items],
    ).model_dump())


@router.post("", summary="新建知识库条目")
def create_entry(
    req: KBEntryCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    entry = KBEntry(**req.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    try:
        chroma_add(entry.id, entry.question, entry.solution, entry.category)
    except Exception:
        pass
    return success(data=KBEntryResponse.model_validate(entry).model_dump(), message="条目已创建")


@router.put("/{entry_id}", summary="更新知识库条目")
def update_entry(
    entry_id: int,
    req: KBEntryUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    entry = db.query(KBEntry).filter(KBEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    for field, value in req.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    try:
        chroma_add(entry.id, entry.question, entry.solution, entry.category)
    except Exception:
        pass
    return success(data=KBEntryResponse.model_validate(entry).model_dump(), message="条目已更新")


@router.delete("/{entry_id}", summary="删除知识库条目")
def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    entry = db.query(KBEntry).filter(KBEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    db.delete(entry)
    db.commit()
    try:
        chroma_delete(entry_id)
    except Exception:
        pass
    return success(message="条目已删除")
