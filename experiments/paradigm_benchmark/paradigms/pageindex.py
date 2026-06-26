"""PageIndex Paradigm (vectorless).

Implementation faithful to the spirit of [1]: structure-based navigation
without dense embeddings. We build a 2-level tree:
  - Root -> category (e.g., "网络连接", "服务器运维")
  - Category -> page_index list
For retrieval:
  1. Tokenize query, score each category by BM25 sum of its pages' tokens
     (using the union of question+solution text per page).
  2. Pick top-1 category, then return its top-K pages by BM25 score
     (BM25 over question text only).
This is an in-memory, GPU-free, deterministic approximation of the
LLM-tree-navigation PageIndex paradigm.

[1] PageIndex: A Vectorless Agentic Document Intelligence Framework (2024).
"""
from __future__ import annotations

import re
import time
from collections import defaultdict

import numpy as np
from rank_bm25 import BM25Okapi

from .base import Hit, IndexStats, Paradigm

_TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.strip()]


class PageIndexParadigm(Paradigm):
    name = "PageIndex"

    def __init__(self, k_categories: int = 3) -> None:
        """V2 公平性：k_categories=3（覆盖 top-3 类别）而非 V1 的 1，
        提升 paraphrase 改写下的类别召回。"""
        self.k_categories = k_categories
        self._entries: list[dict] = []
        self._category_texts: dict[str, list[str]] = defaultdict(list)  # cat -> joined tokens
        self._category_doc_lens: dict[str, int] = {}
        self._bm25_question: BM25Okapi | None = None
        self._avg_doc_len: float = 0.0
        self._build_time = 0.0
        self._index_size = 0

    def build(self, entries: list[dict]) -> IndexStats:
        t0 = time.perf_counter()
        self._entries = entries
        # Build BM25 over question texts (one doc per entry)
        tokenized_questions = [_tokenize(e.get("question", "")) for e in entries]
        # Drop empty token lists with a placeholder so BM25 doesn't crash
        tokenized_questions = [toks if toks else ["_empty_"] for toks in tokenized_questions]
        self._bm25_question = BM25Okapi(tokenized_questions)
        self._avg_doc_len = float(np.mean([len(t) for t in tokenized_questions]))
        # Category inverted index: cat -> combined tokens of question+solution
        cat_tokens: dict[str, list[str]] = defaultdict(list)
        cat_doc_lens: dict[str, int] = defaultdict(int)
        for e in entries:
            cat = str(e.get("category", "_uncategorized_"))
            toks = _tokenize(e.get("question", "")) + _tokenize(e.get("solution", ""))
            cat_tokens[cat].extend(toks)
            cat_doc_lens[cat] += 1
        self._category_texts = dict(cat_tokens)
        self._category_doc_lens = dict(cat_doc_lens)
        self._build_time = time.perf_counter() - t0
        # Approximate size: total tokens (unicode) ~= 2 bytes/token + bookkeeping
        total_chars = sum(sum(len(t) for t in toks) for toks in self._category_texts.values())
        self._index_size = int(total_chars * 2)
        return IndexStats(
            build_time_sec=self._build_time,
            index_size_bytes=self._index_size,
            extra={
                "n_entries": len(entries),
                "n_categories": len(self._category_texts),
                "k_categories": self.k_categories,
            },
        )

    def _score_categories(self, query_tokens: list[str]) -> list[tuple[str, float]]:
        """Score each category by BM25-style IDF-weighted term overlap.

        Approximation: sum of idf-like term frequencies in the category
        corpus. We compute per-category score as
            sum_{t in query_tokens} log(1 + N/df_t) * tf(cat, t)
        where df_t is the number of categories containing t.
        """
        if not query_tokens or not self._category_texts:
            return []
        # Compute per-term df across categories
        df: dict[str, int] = defaultdict(int)
        for cat, toks in self._category_texts.items():
            unique = set(toks)
            for t in query_tokens:
                if t in unique:
                    df[t] += 1
        N = len(self._category_texts)
        cat_tf: dict[str, dict[str, int]] = {
            cat: defaultdict(int) for cat in self._category_texts
        }
        for cat, toks in self._category_texts.items():
            for t in toks:
                cat_tf[cat][t] += 1
        scores: list[tuple[str, float]] = []
        for cat in self._category_texts:
            s = 0.0
            for t in query_tokens:
                if df[t] == 0:
                    continue
                idf = float(np.log(1.0 + N / df[t]))
                s += idf * cat_tf[cat].get(t, 0)
            scores.append((cat, s))
        scores.sort(key=lambda x: -x[1])
        return scores

    def search(self, query: str, query_embedding: list[float], top_k: int) -> list[Hit]:
        if self._bm25_question is None or not self._entries:
            return []
        toks = _tokenize(query)
        if not toks:
            toks = ["_empty_"]
        # Stage 1: pick top-k categories
        cat_scores = self._score_categories(toks)
        chosen_cats = {c for c, _ in cat_scores[: self.k_categories]}
        # Stage 2: BM25 over questions restricted to chosen categories
        scores = self._bm25_question.get_scores(toks)
        # Mask out non-chosen categories
        masked: list[tuple[int, float]] = []
        for idx, e in enumerate(self._entries):
            cat = str(e.get("category", "_uncategorized_"))
            if cat in chosen_cats:
                masked.append((idx, float(scores[idx])))
        masked.sort(key=lambda x: -x[1])
        hits: list[Hit] = []
        for idx, sc in masked[:top_k]:
            hits.append(
                Hit(
                    page_index=int(self._entries[idx]["page_index"]),
                    score=float(sc),
                )
            )
        return hits

    def get_index_size_bytes(self) -> int:
        return self._index_size

    @property
    def is_vector_based(self) -> bool:
        return False
