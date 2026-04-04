"""
RAG 冒烟测试脚本
从 backend/ 目录运行: python smoke_test_rag.py
"""
import sys
import os

# 将 backend/ 加入 Python 路径，使 `from app.xxx import` 可用
sys.path.insert(0, os.path.dirname(__file__))

# 加载项目根目录的 .env 文件
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []


def check(name: str, ok: bool, detail: str = ""):
    status = PASS if ok else FAIL
    print(f"{status} {name}" + (f"  →  {detail}" if detail else ""))
    results.append(ok)


print("\n========== OpsWarden RAG 冒烟测试 ==========\n")

# ── 1. ChromaDB 连接 & 文档数量 ──────────────────────────────
print("【1】ChromaDB 连接与文档数量")
try:
    from app.rag.chroma_client import get_collection
    col = get_collection()
    count = col.count()
    check("ChromaDB 连接正常", True, f"collection='{col.name}'")
    check("知识库非空", count > 0, f"{count} 条文档")
except Exception as e:
    check("ChromaDB 连接正常", False, str(e))
    check("知识库非空", False, "跳过（连接失败）")

print()

# ── 2. 嵌入模型：embed_query ─────────────────────────────────
print("【2】嵌入模型 embed_query()")
try:
    from app.rag.embedder import embed_query
    vec = embed_query("电脑无法开机")
    is_list = isinstance(vec, list) and len(vec) > 0
    check("embed_query 返回向量列表", is_list, f"维度={len(vec)}")
    check("向量元素为 float", isinstance(vec[0], float))
except Exception as e:
    check("embed_query 返回向量列表", False, str(e))
    check("向量元素为 float", False, "跳过")

print()

# ── 3. 嵌入模型：embed_document ──────────────────────────────
print("【3】嵌入模型 embed_document()")
try:
    from app.rag.embedder import embed_document
    vec2 = embed_document("这是一段测试文档内容")
    check("embed_document 返回向量列表", isinstance(vec2, list) and len(vec2) > 0, f"维度={len(vec2)}")
except Exception as e:
    check("embed_document 返回向量列表", False, str(e))

print()

# ── 4. 检索：命中测试 ─────────────────────────────────────────
print("【4】检索命中测试（期望有结果）")
QUERIES_HIT = ["电脑无法开机怎么办", "网络连接不上", "忘记密码如何重置"]
try:
    from app.rag.retriever import search
    for q in QUERIES_HIT:
        docs = search(q, top_k=3, threshold=0.4)
        hit = len(docs) > 0
        detail = f"命中 {len(docs)} 条" if hit else "无命中"
        if hit:
            top = docs[0]
            detail += f"，最高 score={top['score']}，类别={top['category']}"
        check(f"查询「{q}」", hit, detail)
except Exception as e:
    check("检索命中测试", False, str(e))

print()

# ── 5. 检索：阈值过滤测试 ──────────────────────────────────────
print("【5】检索阈值过滤测试（期望无结果或低分被过滤）")
QUERIES_MISS = ["今天天气怎么样", "推荐一部好看的电影"]
try:
    for q in QUERIES_MISS:
        docs = search(q, top_k=3, threshold=0.4)
        filtered = len(docs) == 0
        detail = "已过滤（符合预期）" if filtered else f"意外命中 {len(docs)} 条（score={[d['score'] for d in docs]}）"
        check(f"查询「{q}」过滤", filtered, detail)
except Exception as e:
    check("阈值过滤测试", False, str(e))

print()

# ── 汇总 ──────────────────────────────────────────────────────
total = len(results)
passed = sum(results)
print("=" * 48)
suffix = "全部通过" if passed == total else "存在失败项"
print(f"结果: {passed}/{total} 项通过  {suffix}")
print("=" * 48)
sys.exit(0 if passed == total else 1)
