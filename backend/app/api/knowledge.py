from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models.knowledge import KBEntry
from app.schemas.knowledge import (
    KBEntryCreate,
    KBEntryUpdate,
    KBEntryResponse,
    KBEntryListResponse,
    KBQuickPromptsResponse,
    KBStatsResponse,
)
from app.middleware.auth import get_current_user, require_operator, CurrentUser
from app.utils.response import success
from app.rag.retriever import ingest_kb_entry, prune_anchor_if_unused

router = APIRouter(prefix="/api/knowledge", tags=["知识库"])


@router.get("/stats", summary="知识库统计数据")
def get_stats(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
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


@router.get("/quick-prompts", summary="AI问答快捷提示（仅题目，任意登录用户）")
def quick_prompts(
    limit: int = Query(8, ge=1, le=24),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    rows = (
        db.query(KBEntry.question)
        .order_by(KBEntry.updated_at.desc())
        .limit(limit * 3)
        .all()
    )
    seen: set[str] = set()
    out: list[str] = []
    for (q,) in rows:
        t = (q or "").strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
        if len(out) >= limit:
            break
    return success(data=KBQuickPromptsResponse(questions=out).model_dump())


@router.get("", summary="查询知识库列表")
def list_entries(
    category:    Optional[str] = Query(None),
    source:      Optional[str] = Query(None),
    keyword:     Optional[str] = Query(None),
    doc_id:      Optional[str] = Query(None),
    page:        int = Query(1, ge=1),
    page_size:   int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    q = db.query(KBEntry)
    if category:
        q = q.filter(KBEntry.category == category)
    if source:
        q = q.filter(KBEntry.source == source)
    if doc_id:
        q = q.filter(KBEntry.doc_id == doc_id)
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


@router.delete("/by-doc", summary="按文档标识或页码批量删除条目")
def delete_entries_by_doc(
    doc_id: str = Query(..., min_length=1, max_length=128),
    page_index: Optional[int] = Query(None, ge=1),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    q = db.query(KBEntry).filter(KBEntry.doc_id == doc_id)
    if page_index is not None:
        q = q.filter(KBEntry.page_index == page_index)
    rows = q.all()
    if not rows:
        raise HTTPException(status_code=404, detail="未找到匹配的条目")
    anchor_ids = list({r.anchor_id for r in rows if r.anchor_id})
    for r in rows:
        db.delete(r)
    db.commit()
    for aid in anchor_ids:
        prune_anchor_if_unused(db, aid)
    db.commit()
    return success(message=f"已删除 {len(rows)} 条")


@router.post("", summary="新建知识库条目")
def create_entry(
    req: KBEntryCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    entry = KBEntry(**req.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    emb_warning = None
    try:
        ingest_kb_entry(
            db,
            entry.id,
            entry.question,
            entry.solution,
            entry.category,
            entry.doc_id,
            entry.page_index,
        )
        db.commit()
        db.refresh(entry)
    except Exception as e:
        logger.warning(f"anchor/embedding sync failed for new entry {entry.id}: {e}")
        emb_warning = "条目已保存，但向量同步失败，该条目暂时无法被 AI 检索"
    return success(data=KBEntryResponse.model_validate(entry).model_dump(), message=emb_warning or "条目已创建")


@router.put("/{entry_id}", summary="更新知识库条目")
def update_entry(
    entry_id: int,
    req: KBEntryUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    entry = db.query(KBEntry).filter(KBEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    old_anchor = entry.anchor_id
    for field, value in req.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    emb_warning = None
    try:
        ingest_kb_entry(
            db,
            entry.id,
            entry.question,
            entry.solution,
            entry.category,
            entry.doc_id,
            entry.page_index,
        )
        db.commit()
        db.refresh(entry)
        prune_anchor_if_unused(db, old_anchor)
        db.commit()
    except Exception as e:
        logger.warning(f"anchor/embedding sync failed for update entry {entry.id}: {e}")
        emb_warning = "条目已保存，但向量同步失败，该条目暂时无法被 AI 检索"
    return success(data=KBEntryResponse.model_validate(entry).model_dump(), message=emb_warning or "条目已更新")


@router.delete("/{entry_id}", summary="删除知识库条目")
def remove_kb_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_operator),
):
    entry = db.query(KBEntry).filter(KBEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="条目不存在")
    aid = entry.anchor_id
    db.delete(entry)
    db.commit()
    prune_anchor_if_unused(db, aid)
    db.commit()
    return success(message="条目已删除")
