#!/usr/bin/env python3
"""一次性 KB 重置脚本：删除 kb_entries（及关联 kb_anchors）中来源于 FAQ 的记录，
并可选自动重灌。

项目使用 pgvector，向量分别存于 kb_entries.embedding 与 kb_anchors.anchor_vec
两列上，因此"重置 FAQ"等价于删除 source='faq' 的条目及其级联 anchor 记录。
**source='ticket_writeback' 的工单回写条目会被完整保留。**

用法：
    # 预览（不写库）
    python scripts/reset_kb.py --dry-run

    # 真正清空 FAQ 条目 + 自动调用 load_faq_if_empty 重灌（推荐一步到位）
    python scripts/reset_kb.py --confirm

    # 仅清空 FAQ 条目，不重灌（用于调试，重启 backend 时由 startup 钩子触发重灌）
    python scripts/reset_kb.py --confirm --skip-reload

注意：
- 必须显式指定 --dry-run 或 --confirm，避免误操作
- 重灌过程会下载 embedding 模型（首次）+ 计算 100 条向量，约 30 秒
- 重灌时会调用 ingest_kb_entry，自动写入新的 match_score
- ticket_writeback 等非 FAQ 来源数据不受影响
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# 让脚本在仓库根目录执行时能 import backend 包
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import text  # noqa: E402

from app.database import SessionLocal  # noqa: E402
from app.models.knowledge import KBAnchor, KBEntry  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("reset_kb")


def main() -> int:
    parser = argparse.ArgumentParser(description="重置 FAQ KB：删除 FAQ 来源条目（保留 ticket_writeback）")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="只打印将删除的记录数，不实际写库")
    group.add_argument("--confirm", action="store_true", help="确认执行 TRUNCATE")
    parser.add_argument(
        "--skip-reload",
        action="store_true",
        help="清空后不调用 load_faq_if_empty（仅 --confirm 时生效）",
    )
    args = parser.parse_args()

    started = time.time()

    # FAQ 条目识别：faq_loader.py 入库时写入 doc_id='OpsWarden_FAQ'
    FAQ_DOC_ID = "OpsWarden_FAQ"

    with SessionLocal() as db:
        entry_total = db.query(KBEntry).count()
        faq_entry_count = db.query(KBEntry).filter(KBEntry.doc_id == FAQ_DOC_ID).count()
        other_count = entry_total - faq_entry_count
        anchor_total = db.query(KBAnchor).count()

        logger.info(
            f"当前 KB 状态：kb_entries 共 {entry_total} 行"
            f"（FAQ doc_id='{FAQ_DOC_ID}': {faq_entry_count}，其他保留: {other_count}），"
            f"kb_anchors: {anchor_total} 行（独立向量摘要表，不随 FAQ 删除）"
        )

        if args.dry_run:
            logger.info(
                f"[dry-run] 将删除：doc_id='{FAQ_DOC_ID}' 的 {faq_entry_count} 条 KBEntry；"
                f"其余 {other_count} 条记录（ticket_writeback 等）将被保留。"
                f"kb_anchors 不删除（向量摘要公共表，重灌时 upsert）。未实际写库。"
            )
            return 0

        if faq_entry_count == 0:
            logger.info(f"未找到 doc_id='{FAQ_DOC_ID}' 的条目，无需删除。")
        else:
            logger.warning(
                f"即将删除 doc_id='{FAQ_DOC_ID}' 的 {faq_entry_count} 条 KBEntry"
                f"（anchor_id 外键在 entry 侧，直接删 entry 安全；其他来源数据不受影响）"
            )
            db.execute(
                text("DELETE FROM kb_entries WHERE doc_id = :doc_id"),
                {"doc_id": FAQ_DOC_ID},
            )
            db.commit()

        # 校验
        new_entry = db.query(KBEntry).count()
        logger.info(
            f"删除完成：kb_entries={new_entry} 行（耗时 {time.time() - started:.2f}s）"
        )

        if args.skip_reload:
            logger.info("--skip-reload 已指定：跳过自动重灌。请手动重启 backend 触发 load_faq_if_empty。")
            return 0

        # 自动重灌：直接调 _parse_faq + ingest_kb_entry，绕过 load_faq_if_empty 的
        # count()==0 判空（库里还剩 ticket_writeback 等非 FAQ 条目，count != 0 会被跳过）
        logger.info("开始自动重灌 FAQ……首次会加载 embedding 模型，请耐心等候")
        from pathlib import Path as _Path  # noqa: E402

        from app.models.knowledge import KBEntry as _KBEntry  # noqa: E402
        from app.rag.faq_loader import _parse_faq  # noqa: E402
        from app.rag.retriever import ingest_kb_entry  # noqa: E402

        faq_path = _Path(__file__).resolve().parent.parent / "backend" / "knowledge_base" / "OpsWarden_FAQ.md"
        faq_text = faq_path.read_text(encoding="utf-8")
        parsed = _parse_faq(faq_text)
        if not parsed:
            logger.error("FAQ 解析结果为空，请检查文件格式！")
            return 1

        reload_started = time.time()
        db_entries = []
        for e in parsed:
            obj = _KBEntry(
                category=e["category"],
                question=e["question"],
                solution=e["solution"],
                source="manual",
            )
            db.add(obj)
            db_entries.append(obj)

        db.flush()
        embed_ok = 0
        for idx, obj in enumerate(db_entries, start=1):
            try:
                ingest_kb_entry(db, obj.id, obj.question, obj.solution, obj.category, FAQ_DOC_ID, idx)
                embed_ok += 1
            except Exception as exc:
                logger.warning(f"Embedding sync failed for entry {obj.id}: {exc}")

        db.commit()

        final_entry = db.query(KBEntry).count()
        final_anchor = db.query(KBAnchor).count()
        logger.info(
            f"重灌完成：新增 {len(db_entries)} 条 FAQ（embedding 成功 {embed_ok} 条），"
            f"kb_entries={final_entry} 行，kb_anchors={final_anchor} 行"
            f"（重灌耗时 {time.time() - reload_started:.2f}s，总耗时 {time.time() - started:.2f}s）"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
