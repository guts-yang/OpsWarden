"""A1 多语言 trail 实验：准备 zh / en / mixed 三套 KB 和 query 嵌入。

输入：
  - scripts/eval_datasets/faq_eval_kb_v3.json   （400 KB 条目，zh）
  - scripts/eval_datasets/faq_eval_v3.json      （680 query，zh）

处理：
  - 用 Helsinki-NLP/opus-mt-zh-en 把 KB+query 翻译为英文
  - 用 3 个 embedding 模型对三套 KB 编码：
      zh      : BGE-small-zh  → 512 维
      en      : BGE-small-en  → 384 维
      mixed   : paraphrase-multilingual-MiniLM-L12-v2 → 384 维（双语）

输出：
  - scripts/eval_datasets/v3_expanded/a1_multilingual/
      faq_kb_zh.json  faq_kb_en.json  faq_kb_mixed.json
      faq_queries_zh.json  faq_queries_en.json  faq_queries_mixed.json
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ['HF_HOME'] = 'd:/hf_cache'
CACHE = 'd:/hf_cache'

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
EVAL = SCRIPTS / "eval_datasets"
OUT = EVAL / "v3_expanded" / "a1_multilingual"
OUT.mkdir(parents=True, exist_ok=True)

KB_PATH = EVAL / "faq_eval_kb_v3.json"
QUERY_PATH = EVAL / "faq_eval_v3.json"


def load_json(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  WROTE  {p}  ({p.stat().st_size // 1024} KB)")


# ===== 1. 翻译 =====
def translate_zh_to_en(texts: list[str], batch_size: int = 32) -> list[str]:
    from transformers import MarianMTModel, MarianTokenizer
    print(f"  [translate] loading opus-mt-zh-en ...")
    tok = MarianTokenizer.from_pretrained('Helsinki-NLP/opus-mt-zh-en', cache_dir=CACHE)
    model = MarianMTModel.from_pretrained('Helsinki-NLP/opus-mt-zh-en', cache_dir=CACHE)
    out: list[str] = []
    t0 = time.perf_counter()
    for i in range(0, len(texts), batch_size):
        batch = texts[i: i + batch_size]
        enc = tok(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
        gen = model.generate(**enc, num_beams=2, max_length=512)
        decoded = tok.batch_decode(gen, skip_special_tokens=True)
        out.extend(decoded)
        if (i // batch_size) % 5 == 0:
            print(f"    translated {i + len(batch)} / {len(texts)} ({time.perf_counter() - t0:.1f}s)")
    print(f"  [translate] done in {time.perf_counter() - t0:.1f}s")
    return out


# ===== 2. Embedding =====
def embed_texts(texts: list[str], model_name: str, batch_size: int = 32) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer
    print(f"  [embed] loading {model_name}")
    model = SentenceTransformer(model_name, device='cpu', cache_folder=CACHE)
    try:
        dim = model.get_embedding_dimension()
    except AttributeError:
        dim = model.get_sentence_embedding_dimension()
    print(f"  [embed] dim={dim}  n={len(texts)}")
    vecs = model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vecs.tolist(), dim


# ===== Main =====
def main():
    print("=" * 60)
    print("A1 多语言 trail 数据准备")
    print("=" * 60)

    kb_rows = load_json(KB_PATH)
    q_rows = load_json(QUERY_PATH)
    print(f"  KB: {len(kb_rows)}  Queries: {len(q_rows)}")

    # 合并 question + solution 形成 doc 文本
    kb_texts = [r["question"] + "\n" + r["solution"] for r in kb_rows]
    q_texts = [r["query"] for r in q_rows]

    # 1. 翻译为英文
    en_kb_texts = translate_zh_to_en(kb_texts)
    en_q_texts = translate_zh_to_en(q_texts)

    # 2. 3 套 KB 嵌入
    print("\n--- KB encoding (zh) ---")
    zh_kb_vecs, _ = embed_texts(kb_texts, 'BAAI/bge-small-zh-v1.5')
    print("\n--- KB encoding (en) ---")
    en_kb_vecs, _ = embed_texts(en_kb_texts, 'BAAI/bge-small-en-v1.5')
    print("\n--- KB encoding (mixed / multilingual) ---")
    mx_kb_vecs, _ = embed_texts(kb_texts, 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # 3. 3 套 query 嵌入
    print("\n--- Query encoding (zh) ---")
    zh_q_vecs, _ = embed_texts(q_texts, 'BAAI/bge-small-zh-v1.5')
    print("\n--- Query encoding (en) ---")
    en_q_vecs, _ = embed_texts(en_q_texts, 'BAAI/bge-small-en-v1.5')
    print("\n--- Query encoding (mixed / multilingual) ---")
    mx_q_vecs, _ = embed_texts(q_texts, 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # 4. 保存：KB json + query json
    def with_emb(rows, texts_en, vecs, q_or_kb):
        out = []
        for r, t_en, v in zip(rows, texts_en, vecs):
            x = dict(r)
            x["embedding"] = v
            if q_or_kb == "kb":
                x["question_en"] = t_en  # 翻译后的英文 question
            else:
                x["query_en"] = t_en
            out.append(x)
        return out

    save_json(OUT / "faq_kb_zh.json", with_emb(kb_rows, [t.split('\n')[0] for t in en_kb_texts], zh_kb_vecs, "kb"))
    save_json(OUT / "faq_kb_en.json", with_emb(kb_rows, [t.split('\n')[0] for t in en_kb_texts], en_kb_vecs, "kb"))
    save_json(OUT / "faq_kb_mixed.json", with_emb(kb_rows, [t.split('\n')[0] for t in en_kb_texts], mx_kb_vecs, "kb"))

    save_json(OUT / "faq_queries_zh.json", with_emb(q_rows, en_q_texts, zh_q_vecs, "q"))
    save_json(OUT / "faq_queries_en.json", with_emb(q_rows, en_q_texts, en_q_vecs, "q"))
    save_json(OUT / "faq_queries_mixed.json", with_emb(q_rows, en_q_texts, mx_q_vecs, "q"))

    # 5. README
    readme = f"""# A1 多语言 KB 数据集

- 生成时间：{time.strftime('%Y-%m-%d %H:%M:%S')}
- 来源 KB：faq_eval_kb_v3.json (zh, {len(kb_rows)} 条)
- 来源 query：faq_eval_v3.json (zh, {len(q_rows)} 条)
- 翻译模型：Helsinki-NLP/opus-mt-zh-en
- 三套 embedding：
  - zh     : BAAI/bge-small-zh-v1.5 (512 维)
  - en     : BAAI/bge-small-en-v1.5 (384 维)
  - mixed  : sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 (384 维, 多语言)

## 文件清单

| 文件 | 用途 |
|---|---|
| faq_kb_zh.json | zh KB（已嵌入）|
| faq_kb_en.json | en KB（已嵌入，英文 question 字段 = question_en）|
| faq_kb_mixed.json | 多语言 KB（zh 文本 + multilingual 嵌入）|
| faq_queries_zh.json | zh query（已嵌入）|
| faq_queries_en.json | en query（已嵌入）|
| faq_queries_mixed.json | 多语言 query（zh 文本 + multilingual 嵌入）|
"""
    save_json(OUT / "README.md", readme) if False else (OUT / "README.md").write_text(readme, encoding="utf-8")
    print(f"\n  DONE  A1 data prepared at {OUT}")


if __name__ == "__main__":
    main()
