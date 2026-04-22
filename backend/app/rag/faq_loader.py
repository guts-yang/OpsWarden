import re
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.knowledge import KBEntry
from app.rag.retriever import ingest_kb_entry

logger = logging.getLogger(__name__)

# backend/knowledge_base/OpsWarden_FAQ.md
FAQ_PATH = Path(__file__).parent.parent.parent / "knowledge_base" / "OpsWarden_FAQ.md"


def load_faq_if_empty(db: Session):
    count = db.query(KBEntry).count()
    if count > 0:
        logger.info(f"知识库已有 {count} 条，跳过 FAQ 导入")
        return

    if not FAQ_PATH.exists():
        logger.warning(f"FAQ 文件不存在：{FAQ_PATH}")
        return

    text = FAQ_PATH.read_text(encoding="utf-8")
    entries = _parse_faq(text)

    if not entries:
        logger.warning("FAQ 解析结果为空，请检查文件格式")
        return

    db_entries = []
    for e in entries:
        obj = KBEntry(
            category=e["category"],
            question=e["question"],
            solution=e["solution"],
            source="manual",
            match_score=0.9,
        )
        db.add(obj)
        db_entries.append(obj)

    db.flush()  # Assign IDs without committing

    FAQ_DOC_ID = "OpsWarden_FAQ"
    embed_ok = 0
    for idx, obj in enumerate(db_entries, start=1):
        try:
            ingest_kb_entry(db, obj.id, obj.question, obj.solution, obj.category, FAQ_DOC_ID, idx)
            embed_ok += 1
        except Exception as e:
            logger.warning(f"Embedding sync failed for entry {obj.id}: {e}")

    db.commit()
    logger.info(f"FAQ 已加载：{len(db_entries)} 条，embedding 写入 {embed_ok} 条")


def _parse_faq(text: str) -> list[dict]:
    entries = []
    current_category = "其他"

    blocks = text.split("---")
    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # Update current category if block contains a ## header
        for line in block.splitlines():
            line = line.strip()
            if line.startswith("## "):
                cat = line[3:]
                cat = re.sub(r"（共.*?）", "", cat).strip()   # Remove "（共 18 条）"
                cat = re.sub(r"^[一二三四五六七八九十百]+、", "", cat).strip()  # Remove "一、"
                current_category = cat
                break

        # Skip blocks without Q&A
        if "**问题：**" not in block:
            continue

        # Extract question text
        q_match = re.search(r"\*\*问题：\*\*\s*(.+)", block)
        if not q_match:
            continue
        question = q_match.group(1).strip()

        # Extract solution (everything after **解决方案：**)
        sol_match = re.search(r"\*\*解决方案：\*\*\s*\n?([\s\S]+)", block)
        if not sol_match:
            continue
        solution = sol_match.group(1).strip()

        if question and solution:
            entries.append({
                "category": current_category,
                "question": question,
                "solution": solution,
            })

    return entries
