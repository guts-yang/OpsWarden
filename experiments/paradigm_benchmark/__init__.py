"""RAG Paradigm Comparison Benchmark.

Five paradigms compared on the same dataset/embedding/ground-truth:
- Flat: brute-force cosine
- IVF: pgvector IVFFlat on kb_entries
- HNSW: pgvector HNSW on kb_entries
- PageIndex: vectorless page-tree navigation with BM25
- GridTrace: two-stage grid-quantization retrieval

See docs/PARADIGM_BENCHMARK_DESIGN.md for the academic design.
"""
__version__ = "1.0.0"
