"""V2 数据集扩展：把 faq_eval_kb_v3.json（400 条）真实复制扩展到 N∈{1K,5K,10K,50K}。

设计原则：
  1. **真实复制**：每条 KB 复制 k 次（page_index 递增），保持 BGE 嵌入分布
  2. **文本口语扰动**：30% 概率添加后缀（"怎么办"、"咋整"、"请问一下"），模拟真实员工提问
  3. **嵌入微扰**：σ=0.005 的高斯噪声 + L2 归一化，quant_key 漂移可控
  4. **格式**：1K/5K 用 .json（带 embedding，方便阅读）；10K/50K 用 .npz（紧凑）

输出：
  scripts/eval_datasets/v3_expanded/
    faq_eval_kb_v3_1K.json
    faq_eval_kb_v3_5K.json
    faq_eval_kb_v3_10K.npz
    faq_eval_kb_v3_50K.npz
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
SCRIPTS = ROOT / "scripts"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# 缓存原始 400 条的 embedding，避免每次重新跑 BGE
EMBED_CACHE = Path(__file__).resolve().parent / ".kb_v3_source_embeddings.npz"

logger = logging.getLogger("expand_kb_v3")


def _load_or_compute_source_embeddings(kb_rows: list[dict]) -> np.ndarray:
    """读取或计算 400 条源 KB 的 joint embedding（q+s)/2 + L2-norm）。"""
    if EMBED_CACHE.exists():
        cache = np.load(EMBED_CACHE, allow_pickle=True)
        cached_ids = set(int(x) for x in cache["page_indices"].tolist())
        wanted_ids = set(int(r["page_index"]) for r in kb_rows)
        if wanted_ids.issubset(cached_ids):
            logger.info("Loaded %d cached source embeddings", len(cached_ids))
            # 按 KB 顺序重排
            id_to_emb = {int(p): e for p, e in zip(cache["page_indices"], cache["embeddings"])}
            return np.stack([id_to_emb[int(r["page_index"])] for r in kb_rows], axis=0)

    from app.rag.embedder import embed_document
    from app.rag.eval_engine import compute_joint_embedding

    logger.info("Computing joint embeddings for %d source KB entries via BGE ...", len(kb_rows))
    embs = []
    for i, r in enumerate(kb_rows):
        qv = np.asarray(embed_document(r["question"]), dtype=np.float64)
        sv = np.asarray(embed_document(r["solution"]), dtype=np.float64)
        joint = compute_joint_embedding(qv, sv)
        embs.append(joint)
        if (i + 1) % 50 == 0:
            logger.info("  ... %d / %d", i + 1, len(kb_rows))
    embs = np.stack(embs, axis=0)
    np.savez(
        EMBED_CACHE,
        page_indices=np.asarray([int(r["page_index"]) for r in kb_rows], dtype=np.int32),
        embeddings=embs,
    )
    logger.info("Cached embeddings to %s", EMBED_CACHE)
    return embs


# 真实员工口语化提问的常见尾缀/前缀扰动（30% 概率任选一个）
_SUFFIXES = ["怎么办？", "咋整？", "请问一下", "怎么搞？", "求解答", "怎么处理？"]
_PREFIXES = ["想问一下", "请教下", "问个问题：", "麻烦问下"]


def _perturb_text(text: str, rng: np.random.Generator) -> str:
    """30% 概率添加口语后缀；10% 概率添加口语前缀。保持问题语义。"""
    if not text:
        return text
    out = text
    if rng.random() < 0.3:
        suf = str(rng.choice(_SUFFIXES))
        # 避免重复加同义后缀
        if not any(s in out for s in ["怎么办", "咋整", "请问", "怎么搞", "求解答", "处理"]):
            out = out.rstrip("？?。. ") + suf
    if rng.random() < 0.1:
        pre = str(rng.choice(_PREFIXES))
        if not any(p in out for p in _PREFIXES):
            out = pre + out
    return out


def expand_kb(
    source_kb: list[dict],
    source_embs: np.ndarray,
    target_n: int,
    noise_sigma: float,
    seed: int,
) -> tuple[list[dict], np.ndarray]:
    """把 source 扩展到 target_n 条：保留全部 source + 循环复制补齐。

    每条复制条目：
      - page_index 递增（保证唯一）
      - category 保持
      - question/solution 做轻量口语扰动
      - embedding 加 σ 高斯噪声后 L2-normalize
    """
    rng = np.random.default_rng(seed)
    out_rows: list[dict] = []
    out_embs: list[np.ndarray] = []

    # 1. 保留全部 source（保证真实数据 + 评测查询可命中）
    for r, e in zip(source_kb, source_embs):
        out_rows.append(
            {
                "page_index": int(r["page_index"]),
                "category": r.get("category", ""),
                "question": r["question"],
                "solution": r["solution"],
            }
        )
        out_embs.append(e.astype(np.float64))

    # 2. 循环复制补齐到 target_n
    next_id = max(int(r["page_index"]) for r in source_kb) + 1
    cur = len(source_kb)
    while cur < target_n:
        for r, e in zip(source_kb, source_embs):
            if cur >= target_n:
                break
            perturbed = e + rng.standard_normal(e.shape[0]).astype(np.float64) * noise_sigma
            perturbed = perturbed / (np.linalg.norm(perturbed) + 1e-12)
            out_rows.append(
                {
                    "page_index": next_id,
                    "category": r.get("category", ""),
                    "question": _perturb_text(r["question"], rng),
                    "solution": _perturb_text(r["solution"], rng),
                }
            )
            out_embs.append(perturbed)
            next_id += 1
            cur += 1
    return out_rows, np.stack(out_embs, axis=0).astype(np.float32)


def _write_json(path: Path, rows: list[dict]) -> None:
    """JSON 输出：包含 embedding（list[float]），适合小数据集。"""
    out = []
    for r, e in zip(rows, []):  # placeholder, replaced below
        out.append(r)
    # rows 自带 embedding
    path.write_text(
        json.dumps(rows, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.info("Wrote %d entries to %s (%.1f MB)", len(rows), path, path.stat().st_size / 1024 / 1024)


def _write_npz(path: Path, rows: list[dict], embs: np.ndarray) -> None:
    """NPZ 输出：紧凑格式，适合大数据集（10K/50K）。"""
    np.savez_compressed(
        path,
        page_indices=np.asarray([int(r["page_index"]) for r in rows], dtype=np.int32),
        categories=np.asarray([r.get("category", "") for r in rows]),
        questions=np.asarray([r["question"] for r in rows]),
        solutions=np.asarray([r["solution"] for r in rows]),
        embeddings=embs,
    )
    logger.info("Wrote %d entries to %s (%.1f MB)", len(rows), path, path.stat().st_size / 1024 / 1024)


def main() -> None:
    parser = argparse.ArgumentParser(description="Expand faq_eval_kb_v3 to N∈{1K,5K,10K,50K}")
    parser.add_argument(
        "--source",
        default=str(SCRIPTS / "eval_datasets" / "faq_eval_kb_v3.json"),
        help="源 KB 路径（默认 400 条 v3）",
    )
    parser.add_argument(
        "--output-dir",
        default=str(SCRIPTS / "eval_datasets" / "v3_expanded"),
        help="输出目录",
    )
    parser.add_argument(
        "--target-sizes",
        default="1000,5000,10000,50000",
        help="目标规模（逗号分隔）",
    )
    parser.add_argument(
        "--noise-sigma",
        type=float,
        default=0.005,
        help="embedding 噪声 σ（默认 0.005）",
    )
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_kb = json.loads(Path(args.source).read_text(encoding="utf-8"))
    logger.info("Source KB: %d entries from %s", len(source_kb), args.source)

    source_embs = _load_or_compute_source_embeddings(source_kb)

    sizes = [int(s) for s in args.target_sizes.split(",")]
    for n in sizes:
        logger.info("=" * 50)
        logger.info("Expanding to N=%d ...", n)
        rows, embs = expand_kb(source_kb, source_embs, n, args.noise_sigma, args.seed)
        if n <= 5000:
            # 小数据集：JSON（含 embedding）便于阅读
            # 注入 embedding 字段
            rows_with_emb = []
            for r, e in zip(rows, embs):
                rr = dict(r)
                rr["embedding"] = e.tolist()
                rows_with_emb.append(rr)
            out_path = out_dir / f"faq_eval_kb_v3_{n}.json"
            _write_json(out_path, rows_with_emb)
        else:
            # 大数据集：NPZ（紧凑）
            out_path = out_dir / f"faq_eval_kb_v3_{n}.npz"
            _write_npz(out_path, rows, embs)
    logger.info("All done. Output: %s", out_dir)


if __name__ == "__main__":
    main()
