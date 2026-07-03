#!/usr/bin/env python3
"""Build RAG eval dataset v2: exact + paraphrase + negative.

Usage (from repo root):
    python scripts/build_eval_dataset_v2.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
OUTPUT = ROOT / "scripts" / "eval_datasets" / "faq_eval_v2.json"

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.rag.faq_loader import FAQ_PATH, _parse_faq  # noqa: E402

NEGATIVE_QUERIES = [
    # From presentation/rag-interactive.html (hit:false)
    "会议室投影仪连不上笔记本",
    "公司食堂几点开门",
    "如何申请年假报销差旅费",
    # Out-of-domain / not in FAQ
    "今天天气怎么样",
    "帮我写一份周报",
    "股票今天涨了吗",
    "附近有什么好吃的餐厅",
    "怎么订机票和酒店",
    "Python 怎么学比较快",
    "春节放假安排是什么",
    "工资什么时候发",
    "公司年会什么时候开",
    "如何办理居住证",
    "小孩入学需要什么材料",
    "哪里可以打印文件",
    "快递寄到公司填什么地址",
    "健身房会员卡怎么办",
    "停车位怎么申请",
    "办公室空调太冷找谁",
    "咖啡机坏了谁负责修",
    "团建活动怎么报名",
    "出差补贴标准是多少",
    "劳动合同到期怎么续签",
    "医保报销流程是什么",
    "如何投诉物业",
    "装修办公室要哪些审批",
    "访客登记怎么操作",
    "公司班车时刻表在哪看",
    "邮件群发有什么规范",
    "VPN 在国外能用吗",
    "能不能自带电脑上班",
    "公司股票期权怎么兑现",
]


def _strip_question_prefix(q: str) -> str:
    q = q.strip()
    for prefix in ("请问", "如何", "怎样", "怎么"):
        if q.startswith(prefix):
            q = q[len(prefix) :].lstrip("，,：: ")
            break
    return q


def paraphrase_a(question: str) -> str:
    """Rule A: drop formal prefix, append colloquial suffix."""
    core = _strip_question_prefix(question).rstrip("？?")
    if not core:
        return question
    return f"{core}怎么办？"


def paraphrase_b(question: str) -> str:
    """Rule B: shorter oral form with '要咋处理'."""
    core = _strip_question_prefix(question).rstrip("？?")
    if len(core) > 18:
        # keep first clause before comma or first 14 chars
        parts = re.split(r"[，,；;]", core)
        core = parts[0].strip()
        if len(core) > 16:
            core = core[:16].rstrip("的、与及和")
    if not core:
        return question
    return f"{core}要咋处理？"


def build_dataset_v2() -> list[dict]:
    if not FAQ_PATH.exists():
        raise FileNotFoundError(FAQ_PATH)

    parsed = _parse_faq(FAQ_PATH.read_text(encoding="utf-8"))
    rows: list[dict] = []

    for idx, item in enumerate(parsed, start=1):
        q = item["question"].strip()
        cat = item["category"]
        rows.append(
            {
                "query": q,
                "page_index": idx,
                "split": "exact",
                "paraphrase_id": None,
                "category": cat,
                "question": q,
                "solution": item["solution"],
            }
        )
        pa = paraphrase_a(q)
        pb = paraphrase_b(q)
        if pa != q:
            rows.append(
                {
                    "query": pa,
                    "page_index": idx,
                    "split": "paraphrase",
                    "paraphrase_id": f"p{idx}_a",
                    "category": cat,
                    "question": q,
                    "solution": item["solution"],
                }
            )
        if pb != q and pb != pa:
            rows.append(
                {
                    "query": pb,
                    "page_index": idx,
                    "split": "paraphrase",
                    "paraphrase_id": f"p{idx}_b",
                    "category": cat,
                    "question": q,
                    "solution": item["solution"],
                }
            )

    for i, nq in enumerate(NEGATIVE_QUERIES, start=1):
        rows.append(
            {
                "query": nq,
                "page_index": None,
                "split": "negative",
                "paraphrase_id": f"n{i}",
                "category": None,
                "question": None,
                "solution": None,
            }
        )

    return rows


def main() -> int:
    dataset = build_dataset_v2()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    n_exact = sum(1 for r in dataset if r["split"] == "exact")
    n_para = sum(1 for r in dataset if r["split"] == "paraphrase")
    n_neg = sum(1 for r in dataset if r["split"] == "negative")
    print(f"Wrote {len(dataset)} rows to {OUTPUT}")
    print(f"  exact={n_exact} paraphrase={n_para} negative={n_neg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
