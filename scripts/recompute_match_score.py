#!/usr/bin/env python3
"""一次性回填脚本：为存量 KBEntry 重新计算「自检质量分」(match_score)。

自检质量分 = BGE 模型对 question 与 solution 的向量余弦相似度（clip 到 [0, 1]）。
适用场景：
  - 历史数据中 match_score 仍为旧的硬编码值（0.9 / 0.8）
  - 调整了 EMBEDDING_MODEL 后需要全量重算

用法（在仓库根目录执行）：
    python scripts/recompute_match_score.py                 # 全量回填
    python scripts/recompute_match_score.py --dry-run       # 仅打印不写库
    python scripts/recompute_match_score.py --batch-size 50 # 自定义批量提交大小
    python scripts/recompute_match_score.py --only-legacy   # 仅回填 match_score in (0.9, 0.8) 的旧值

注意：脚本独立运行，不会影响主服务；首次加载 BGE 模型会有几秒延时。
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import numpy as np

# 让脚本在仓库根目录执行时能 import backend 包
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.database import SessionLocal  # noqa: E402
from app.models.knowledge import KBEntry  # noqa: E402
from app.rag.embedder import embed_document  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("recompute_match_score")

LEGACY_VALUES = {0.9, 0.8}


def compute_score(question: str, solution: str) -> float:
    q = (question or "").strip()
    s = (solution or "").strip()
    if not q or not s:
        return 0.0
    try:
        qv = np.asarray(embed_document(q), dtype=np.float64)
        sv = np.asarray(embed_document(s), dtype=np.float64)
        sim = float(np.dot(qv, sv))
    except Exception as ex:
        logger.warning(f"embed failed: {ex}")
        return 0.0
    if not np.isfinite(sim):
        return 0.0
    return max(0.0, min(1.0, sim))


def main() -> int:
    parser = argparse.ArgumentParser(description="重新计算 KBEntry.match_score（自检质量分）")
    parser.add_argument("--dry-run", action="store_true", help="仅打印结果，不写入数据库")
    parser.add_argument("--batch-size", type=int, default=20, help="批量提交大小，默认 20")
    parser.add_argument(
        "--only-legacy",
        action="store_true",
        help="仅处理 match_score 仍为历史硬编码值 (0.9 / 0.8) 的条目",
    )
    args = parser.parse_args()

    if args.batch_size < 1:
        logger.error("--batch-size 必须 >= 1")
        return 2

    started = time.time()
    total = 0
    updated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as db:
        q = db.query(KBEntry).order_by(KBEntry.id.asc())
        all_entries = q.all()
        total = len(all_entries)
        logger.info(f"扫描到 KBEntry 共 {total} 条")

        pending = 0
        for idx, entry in enumerate(all_entries, start=1):
            if args.only_legacy:
                old = float(entry.match_score) if entry.match_score is not None else -1.0
                # 浮点比对兜底，允许 0.0001 误差
                if not any(abs(old - v) < 1e-4 for v in LEGACY_VALUES):
                    skipped += 1
                    continue

            try:
                new_score = compute_score(entry.question, entry.solution)
            except Exception as ex:
                logger.warning(f"entry id={entry.id} 计算失败：{ex}")
                failed += 1
                continue

            old_score = float(entry.match_score) if entry.match_score is not None else None
            logger.info(
                f"[{idx}/{total}] id={entry.id} doc_id={entry.doc_id} page={entry.page_index} "
                f"old={old_score} -> new={new_score:.4f}"
            )

            if not args.dry_run:
                entry.match_score = round(new_score, 4)
                pending += 1
                if pending >= args.batch_size:
                    db.commit()
                    pending = 0
            updated += 1

        if not args.dry_run and pending > 0:
            db.commit()

    elapsed = time.time() - started
    logger.info(
        f"完成：扫描 {total} 条，更新 {updated} 条，跳过 {skipped} 条，"
        f"失败 {failed} 条，耗时 {elapsed:.2f}s"
        + ("（dry-run，未实际写库）" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
