# A1 多语言 KB 数据集

- 生成时间：2026-06-25 13:50:53
- 来源 KB：faq_eval_kb_v3.json (zh, 400 条)
- 来源 query：faq_eval_v3.json (zh, 680 条)
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
