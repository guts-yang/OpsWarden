# A2 trail 用户感知评分 — 受试者用表

_生成时间：2026-06-25 13:57:57_

## 受试者说明

**任务**：对 30 条 query 评估 5 个范式的输出，回答 3 个维度（每条 0-5 分）：
1. **causality（召回原因可理解性）**：看解释能否理解「为什么这条被召回」
2. **trust（结果可信度）**：看解释能否判断「这条结果是否可信」
3. **debuggability（失败定位）**：看解释能否帮助定位「为何召回失败 / 召回错误」

**评分标准**：
- 0 = 完全无法判断 / 无信息
- 1 = 几乎无帮助
- 2 = 部分信息但不够
- 3 = 一般
- 4 = 较好
- 5 = 完全能理解 / 充分可信 / 容易定位

---

## Query 1: 账号被冻结后如何自助解冻或申请人工处理？

**类型**：正样本（ground_truth = page #1）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #3 (score=0.90, type=main)
  - 桶 #2 (score=0.89, type=main)
  - 桶 #0 (score=0.89, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #1, score=0.908

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.908
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #1, score=0.908

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.908
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #1, score=0.908

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.908
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #1, score=0.908

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=7.417

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 2: 账号被冻结后如何自助解冻或申请人工处理怎么办？

**类型**：正样本（ground_truth = page #1）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #3 (score=0.91, type=main)
  - 桶 #2 (score=0.89, type=main)
  - 桶 #0 (score=0.89, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #1, score=0.912

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.912
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #1, score=0.912

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.912
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #1, score=0.912

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.912
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #1, score=0.912

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=8.168

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 3: 账号被冻结后如何自助解冻或申请人要咋处理？

**类型**：正样本（ground_truth = page #1）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #3 (score=0.89, type=main)
  - 桶 #0 (score=0.88, type=main)
  - 桶 #2 (score=0.88, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.896
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.896
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.896
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 4: 账号被冻结后如何自助解冻或申请人工处理咋整

**类型**：正样本（ground_truth = page #1）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #3 (score=0.89, type=main)
  - 桶 #2 (score=0.88, type=main)
  - 桶 #0 (score=0.88, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #1, score=0.901

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.901
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #1, score=0.901

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.901
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #1, score=0.901

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.901
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #1, score=0.901

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 5: 想问下账号被冻结后如何自助解冻或申请人工处理有没有办法处理？

**类型**：正样本（ground_truth = page #1）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #3 (score=0.89, type=main)
  - 桶 #2 (score=0.88, type=main)
  - 桶 #1 (score=0.87, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.896
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.896
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.896
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #1, score=0.896

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 6: 忘记密码后如何通过短信验证码重置新密码？

**类型**：正样本（ground_truth = page #2）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #5 (score=0.89, type=main)
  - 桶 #7 (score=0.89, type=main)
  - 桶 #6 (score=0.88, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #2, score=0.894

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.894
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #2, score=0.894

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.894
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #2, score=0.894

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.894
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #2, score=0.894

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #2, score=7.417

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 7: 忘记密码后如何通过短信验证码重置新密码怎么办？

**类型**：正样本（ground_truth = page #2）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #7 (score=0.90, type=main)
  - 桶 #5 (score=0.89, type=main)
  - 桶 #6 (score=0.88, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #2, score=0.903

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.903
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #2, score=0.903

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.903
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #2, score=0.903

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.903
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #2, score=0.903

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #2, score=8.168

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 8: 忘记密码后如何通过短信验证码重置要咋处理？

**类型**：正样本（ground_truth = page #2）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #7 (score=0.85, type=main)
  - 桶 #5 (score=0.83, type=main)
  - 桶 #6 (score=0.83, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #2, score=0.853

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.853
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #2, score=0.853

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.853
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #2, score=0.853

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.853
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #2, score=0.853

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 9: 忘记密码后如何通过短信验证码重置新密码咋整

**类型**：正样本（ground_truth = page #2）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #7 (score=0.87, type=main)
  - 桶 #5 (score=0.87, type=main)
  - 桶 #6 (score=0.86, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #2, score=0.875

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.875
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #2, score=0.875

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.875
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #2, score=0.875

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.875
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #2, score=0.875

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 10: 想问下忘记密码后如何通过短信验证码重置新密码有没有办法处理？

**类型**：正样本（ground_truth = page #2）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #7 (score=0.87, type=main)
  - 桶 #5 (score=0.86, type=main)
  - 桶 #6 (score=0.86, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #2, score=0.873

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.873
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #2, score=0.873

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.873
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #2, score=0.873

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.873
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #2, score=0.873

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 11: 如何申请新系统的访问权限并完成审批？

**类型**：正样本（ground_truth = page #3）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #8 (score=0.87, type=main)
  - 桶 #9 (score=0.85, type=main)
  - 桶 #11 (score=0.84, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #3, score=0.881

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.881
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #3, score=0.881

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.881
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #3, score=0.881

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.881
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #3, score=0.881

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #3, score=8.168

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 12: 申请新系统的访问权限并完成审批怎么办？

**类型**：正样本（ground_truth = page #3）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #11 (score=0.88, type=main)
  - 桶 #8 (score=0.88, type=main)
  - 桶 #9 (score=0.87, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #3, score=0.888

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.887
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #3, score=0.887

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.888
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #3, score=0.888

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.888
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #3, score=0.888

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #3, score=8.168

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 13: 申请新系统的访问权限并完成审批要咋处理？

**类型**：正样本（ground_truth = page #3）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #11 (score=0.86, type=main)
  - 桶 #9 (score=0.85, type=main)
  - 桶 #8 (score=0.85, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #3, score=0.868

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.868
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #3, score=0.868

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.868
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #3, score=0.868

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.868
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #3, score=0.868

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 14: 申请新系统的访问权限并完成审批咋整

**类型**：正样本（ground_truth = page #3）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #9 (score=0.86, type=main)
  - 桶 #11 (score=0.85, type=main)
  - 桶 #8 (score=0.85, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #3, score=0.861

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.861
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #3, score=0.861

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.861
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #3, score=0.861

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.861
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #3, score=0.861

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 15: 想问下申请新系统的访问权限并完成审批有没有办法处理？

**类型**：正样本（ground_truth = page #3）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #11 (score=0.82, type=main)
  - 桶 #9 (score=0.81, type=main)
  - 桶 #10 (score=0.81, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #3, score=0.828

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.828
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #3, score=0.828

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.828
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #3, score=0.828

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.828
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #3, score=0.828

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 16: 管理员如何为新员工开通运维账号并下发初始密码？

**类型**：正样本（ground_truth = page #4）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #13 (score=0.92, type=main)
  - 桶 #12 (score=0.92, type=main)
  - 桶 #15 (score=0.92, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #4, score=0.928

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.928
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #4, score=0.928

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.928
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #4, score=0.928

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.928
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #4, score=0.928

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #4, score=7.417

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 17: 管理员如何为新员工开通运维账号并下发初始密码怎么办？

**类型**：正样本（ground_truth = page #4）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #15 (score=0.93, type=main)
  - 桶 #13 (score=0.92, type=main)
  - 桶 #12 (score=0.92, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #4, score=0.941

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.941
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #4, score=0.941

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.941
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #4, score=0.941

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.941
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #4, score=0.941

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #4, score=8.168

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 18: 管理员如何为新员工开通运维账号并要咋处理？

**类型**：正样本（ground_truth = page #4）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #15 (score=0.83, type=main)
  - 桶 #13 (score=0.82, type=main)
  - 桶 #14 (score=0.82, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #4, score=0.831

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.831
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #4, score=0.831

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.831
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #4, score=0.831

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.831
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #4, score=0.831

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 19: 会议室投影仪连不上笔记本

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #359 (score=0.73, type=main)
  - 桶 #357 (score=0.72, type=main)
  - 桶 #358 (score=0.72, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #90, score=0.736

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.736
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #90, score=0.736

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.736
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #90, score=0.736

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.736
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #90, score=0.736

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 20: 公司食堂几点开门

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.465
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #97, score=0.465

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.465
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #97, score=0.465

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 21: 如何申请年假报销差旅费

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（8 个）：
  - 桶 #377 (score=0.63, type=main)
  - 桶 #378 (score=0.62, type=main)
  - 桶 #376 (score=0.61, type=main)
📊 L1 候选数：8 | 平均桶大小：1.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #95, score=0.631

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: 0.631
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #95, score=0.631

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.631
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #95, score=0.631

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.631
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #95, score=0.631

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 22: 今天天气怎么样

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.375
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #8, score=0.375

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.375
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #8, score=0.375

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 23: 帮我写一份周报

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.449
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #56, score=0.449

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.449
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #56, score=0.449

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 24: 股票今天涨了吗

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.38
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #7, score=0.38

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.38
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #7, score=0.38

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 25: 附近有什么好吃的餐厅

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.246
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #24, score=0.246

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.246
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #24, score=0.246

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 26: 怎么订机票和酒店

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.482
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #95, score=0.482

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.482
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #95, score=0.482

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 27: Python 怎么学比较快

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.501
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #57, score=0.501

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.501
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #57, score=0.501

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 28: 春节放假安排是什么

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.447
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #99, score=0.447

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.447
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #99, score=0.447

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 29: 工资什么时候发

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.466
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #88, score=0.466

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.466
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #88, score=0.466

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---

## Query 30: 公司年会什么时候开

**类型**：负样本（不应召回）

### GridTrace+

🔍 **GridTrace+ L1 锚点命中**（0 个）：

📊 L1 候选数：0 | 平均桶大小：0.0
⚙️ 扩展环触发：False（新增 0 桶）
🎯 L3 Rerank 触发：False（候选 0）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### GridTrace

🔍 **GridTrace（无增强）** 单层量化匹配
📊 返回 top-1 score: None
（无 trail 字段，无扩展环 / rerank）

**Top-1 召回**：page #None, score=None

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### HNSW

🚀 **HNSW KNN 图检索** (M=16, ef_search=200)
📊 返回 top-1 score: 0.399
❌ 无任何 trail 字段——无法追溯「为什么这条被召回」

**Top-1 召回**：page #88, score=0.399

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### IVF

🗂️ **IVF 倒排聚类** (n_probe=8)
📊 返回 top-1 score: 0.399
❌ 无 trail——只知 score，不知经过哪几个聚类

**Top-1 召回**：page #88, score=0.399

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

### PageIndex

📑 **PageIndex 类别树 + BM25**
📊 命中类别：None
（BM25 关键词匹配路径，可解释性中等）

**Top-1 召回**：page #1, score=0.0

**评分**（请打分 0-5）：

| 维度 | 评分 (0-5) |
|---|---|
| causality 召回原因可理解性 | ___ |
| trust 结果可信度 | ___ |
| debuggability 失败定位 | ___ |

---
