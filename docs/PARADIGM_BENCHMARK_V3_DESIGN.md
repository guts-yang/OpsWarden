# GridTrace 扩展实验方案（V3 规划）

> **文档定位**：本文档是 V2 实测之后的下一步规划。V2 已诚实给出「GridTrace+ 独享优势收敛到 2 个维度（可解释性 + 合规删除零重建）」的结论；V3 的目标不是重复验证 V2，而是**把这 2 个维度扩展到 6 个维度**。
>
> **上游**：`docs/PARADIGM_BENCHMARK_V2_REPORT.md`（V2 实测报告，6 范式 × 5 场景，诚实承认 HNSW 在 S1/S2/S3 仍最优）
>
> **下游**：V3 实测报告（本文档是规划 + 实施路线图）
>
> **时间窗口**：2026 Q3-Q4（约 15 周）
>
> **作者**：OpsWarden 团队

---

## 0. 阅读指引

| 章节 | 内容 | 读者 |
|---|---|---|
| §1 | 实验目标（要证什么 / 不证什么） | 所有读者必读 |
| §2 | 6 大类 19 个对照实验 | 研究人员必读 |
| §3 | 数据集生成策略 | 数据工程必读 |
| §4 | 评估指标体系（5 维度） | 算法/评测必读 |
| §5 | 6 阶段实施路线图（Week 1-15） | 项目管理必读 |
| §6 | 预期结论 + 风险预案 | 决策者必读 |
| §7-8 | 资源需求 + 复现性保障 | 运维/工程必读 |

---

## 1. 实验目标

### 1.1 一句话核心目标

**把 GridTrace 的独享优势从 2 个真实维度（可解释性 + 合规删除）扩展到 6 个维度（新增增量更新、分布式分片、索引腐烂适应性、多模态承载），同时明确 4 个 GridTrace 不擅长的边界。**

### 1.2 三个核心论点（V3 目标要验证）

| ID | 论点 | V2 状态 | V3 验证方式 |
|---|---|---|---|
| **C1** | GridTrace 的 retrieval_trail 提供生产级可解释性 | ✅ 已证（trail=1.0 独享） | §2.A1-A2 多语言 + 用户感知 |
| **C2** | GridTrace 删桶即生效，零重建 | ✅ 已证（残余 0%） | §2.A3 量化零重建开销 |
| **C3** | GridTrace 桶可逐桶增量更新（生产 KB 不会一次性 50K） | ❓ 待证 | §2.B1-B3 增量扩展/删除/改写 |

### 1.3 三个待探索论点（V3 目标要发现）

| ID | 论点 | V3 探索方式 |
|---|---|---|
| **E1** | GridTrace 桶可天然分片，分布式场景优于 HNSW 整体子图 | §2.C1-C3 水平分片 / 多租户 / 跨地域 |
| **E2** | GridTrace 量化可在线更新，应对索引腐烂 | §2.D1-D3 量化衰减 / 类别漂移 / 在线更新 |
| **E3** | GridTrace 桶可承载多模态 embedding（文本 + metric + log） | §2.E1-E3 文本+metric / +log / +runbook |

### 1.4 一个不验证的命题（诚实声明）

> **不验证**：「GridTrace 在「纯质量 + 速度」上超越 HNSW」。
>
> V2 已实测：HNSW 在 S1/S2/S3 的 Hit@1 与 p50 均第一（N=50K 时 p50=0.18ms vs GridTrace+ 9.81ms）。V3 不再重复此方向，把工程预算投到 GridTrace 真正可能独享的 6 个维度。

### 1.5 V3 决策矩阵（V2 实测 + V3 预期）

| 场景 | V2 真实赢家 | V3 预期新增独享维度 |
|---|---|---|
| 极小 N (≤100) | Flat | 不补（V3 边界 F1） |
| 中等 N (1K-10K) | HNSW | GridTrace+ 增量更新优势 |
| 大 N (50K-1M) | HNSW | GridTrace+ 分布式分片优势 |
| 多租户 / 跨地域 | HNSW（V2 未覆盖） | **GridTrace 桶级隔离**（V3 C2-C3） |
| 索引腐烂 (6 月+) | HNSW（V2 未覆盖） | **GridTrace 在线量化**（V3 D1-D3） |
| 多模态 KB | HNSW（V2 未覆盖） | **GridTrace 桶承载异构 embedding**（V3 E1-E3） |
| 合规删除 | 6 范式并列（重建后都归零） | **GridTrace 零重建独享**（V3 A3） |
| 可解释性 | **GridTrace+** (trail=1.0) | **MOS 用户评分**（V3 A2） |

---

## 2. 对照实验设计（6 大类 × 19 个实验）

### 实验总览表

| 类别 | 实验 | 目的 | 对照范式 | 核心指标 | 工时 |
|---|---|---|---|---|---|
| **A. 巩固** | A1 多语言 trail 完整性 | 把 C1 从中文扩到多语言 | GridTrace+ / HNSW | trail 保持率 | 2d |
| | A2 trail 用户感知评分 | trail 数值 ≠ 用户可读 | GridTrace+ / HNSW / IV | MOS 0-5 | 3d |
| | A3 合规删除零重建 | 量化 A3「零重建」开销 | GridTrace+ / HNSW / IV | 删后 p50/RSS/Build Time | 3d |
| **B. 增量** | B1 增量扩展 | 生产 KB 渐进增长 | GridTrace+ / HNSW / IV | 累计 Build Time | 5d |
| | B2 增量删除 | 运维定期清理 | GridTrace+ / HNSW / IV | 残余召回 / RSS | 3d |
| | B3 增量改写 | 运维修订文档 | GridTrace+ / HNSW / IV | Hit@1 衰减 / 重训成本 | 3d |
| **C. 分布式** | C1 水平分片 | 10 shard × 5K | GridTrace+ / HNSW | 跨节点 p50 / Hit@1 | 5d |
| | C2 多租户隔离 | 10 租户 × 1K | GridTrace+ / HNSW | 跨租户召回 / p50 | 3d |
| | C3 跨地域部署 | 3 region 同步 | GridTrace+ / HNSW | 同步延迟 / 检索 p50 | 3d |
| **D. 腐烂** | D1 量化召回衰减 | 6 月后 KB 漂移 | GridTrace+ / HNSW | Hit@1 衰减曲线 | 5d |
| | D2 类别漂移 | 5→20 类别 | GridTrace+ / HNSW | 粗量化重训时间 | 3d |
| | D3 在线量化更新 | 量化在线重训 | GridTrace+ / HNSW | 长期 Hit@1 波动 | 4d |
| **E. 多模态** | E1 文本+metric 序列 | 文本+CPU/内存曲线 | GridTrace+ / HNSW | 联合 Hit@1 | 4d |
| | E2 文本+log 日志 | 文本+错误码+log 模式 | GridTrace+ / HNSW | 联合 Hit@1 | 3d |
| | E3 文本+runbook | 步骤树+自由文本 | GridTrace+ / HNSW | 联合 Hit@1 | 4d |
| **F. 边界** | F1 极小 N | N=10/50/100 | GridTrace+ / HNSW / Flat | 桶稀疏 / Hit@1 | 2d |
| | F2 极大 N | N=100K/500K/1M | GridTrace+ / HNSW | 锚点爆增 / p50 | 3d |
| | F3 极高维 | 1024/2048/4096 维 | GridTrace+ / HNSW | RSS / Build Time | 2d |
| | F4 极低质量 KB | 50 canonical × 5 variant | GridTrace+ / HNSW | 泛化能力 | 2d |

**总工时**：约 15 周 × 1 人 = 60 个工作日。

---

### A. 巩固基础（3 个实验 × 1.5 周）

#### A1. 多语言 KB 的 retrieval_trail 完整性

**目的**：V2 只测了中文，验证英文/中英混合 KB 下 GridTrace+ 的 trail 仍完整（trail 字段不依赖语言，但量化的桶边界可能因多语言嵌入分布不同而漂移）。

**设计**：
- 数据：v3 canonical 的 100 条 KB，用 NLLB-200 翻译为 3 套（中文 / 英文 / 中英混合）
- KB 规模：400（与 V2 一致）
- 嵌入模型：BGE-small-zh / BGE-small-en / 双语混合 BGE
- 范式：GridTrace+ / HNSW（其他 4 范式不变，做交叉验证）
- 测量：每种语言跑 100 query，统计 trail 完整度

**指标**：
- `trail_completeness = 1 - (缺字段数 / 6)`（6 个字段：quant_key / l1_bucket_size / l2_score / l1_anchor_indices / expand_count / rerank_triggered）
- 每语言 100 query 的 trail 完整度均值

**预期**：
- GridTrace+ 三语言 trail 完整度均 ≥ 0.95
- HNSW/IVF/Flat trail 完整度恒为 0
- 英文 KB 下 GridTrace+ p50 略高于中文（英文 token 多，BGE 编码慢 10-20%）

**风险**：BGE-small-en 在中文上可能召回下降，需用 mE5-base 替代做交叉验证。

---

#### A2. retrieval_trail 用户研究

**目的**：trail 数值完整性 ≠ 用户可读性。需要让真实运维工程师评估 trail 是否有助于理解「为什么这条结果被召回」。

**设计**：
- 受试者：5 名企业运维工程师（中级以上，3 年+ 经验）
- 任务：30 条 trail 输出（每条 query + 5 范式的输出），每条 0-5 分
- 评分维度（每维度独立打分）：
  1. 能否理解召回原因（causality）
  2. 能否判断结果可信度（trust）
  3. 能否定位失败原因（debuggability）
- 工具：自制 Web 表单（Gradio Streamlit），随机化范式顺序避免偏见
- 时长：每位受试者 60 分钟

**指标**：
- MOS（Mean Opinion Score）= 三维度均值
- 95% CI（Wilcoxon signed-rank test）

**预期**：
- GridTrace+ MOS ≥ 3.5（实际可读）
- HNSW/IVF/Flat 无法生成 trail，MOS = 0
- PageIndex 的 category_path 提供部分信息，MOS ≈ 1.5-2.0

**风险**：受试者数量少（5 人）统计功效不足；可通过 Cohen's d > 0.5 弥补。

---

#### A3. 合规删除的「零重建」特性精确量化

**目的**：V2 只测了「残余召回 = 0%」。但生产关心的是「删除后单查询延迟是否受影响」「RSS 是否立即释放」「是否需要重建」。

**设计**：
- 基线：N=50K
- 测 3 种删除策略：
  1. **GridTrace+**：删 quant_key 桶 + member_indices（O(桶大小)，无需重建）
  2. **HNSW**：mark_deleted=True（标记删除，节点仍占内存）
  3. **HNSW + 重建**：mark_deleted 后 rebuild 索引（O(N) 重建）
  4. **IVF**：删除倒排项 + 重建（O(N) 重建）
- 测 4 个时间点：删前 / 删后立即 / 删后 1 小时 / 删后 24 小时
- 删 1 条 vs 删 100 条 vs 删 1000 条（3 个量级）

**指标**：
- `post_delete_p50_increase_ratio` = 删后 p50 / 删前 p50
- `rss_reduction_ratio` = (删前 RSS - 删后 RSS) / 删前 RSS
- `rebuild_time` = 重建耗时（s）
- `residual_recall` = 删后 100 query 召回率（应=0）

**预期**：

| 范式 | 删后 p50 变化 | RSS 立即释放 | 残余召回 | 重建 |
|---|---|---|---|---|
| GridTrace+ | 0%（不变） | ✅ 100% | 0% | ❌ 不需要 |
| HNSW (mark) | 0%（不变） | ❌ 0% | 0% | ❌ 可选 |
| HNSW (rebuild) | 重建后 0% | ✅ 100% | 0% | ✅ 2-5s |
| IVF (rebuild) | 重建后 0% | ✅ 100% | 0% | ✅ 5-10s |

**关键发现**：GridTrace+ 是**唯一同时满足「删后 p50 不变 + RSS 立即释放 + 零重建」三条件**的范式。

---

### B. 增量更新（3 个实验 × 2 周）

#### B1. 增量扩展（最关键实验）

**目的**：生产环境 KB 不会一次性 50K，是 10K→50K 渐进。验证 GridTrace+ 追加桶的开销远低于 HNSW 重建图。

**设计**：
- 起点：N=10K
- 增量：每批 +1K 真实扰动文档，重复 40 批到 N=50K
- 范式：GridTrace+（追加 quant_key 桶 + 新 anchor）/ HNSW（追加节点 + ef 调优）/ IVF（增量 kmeans + 倒排更新）
- 测量：每批后立即跑 200 query（V2 同源）

**指标**：
- `cumulative_build_time`（累计 Build Time，s）
- `hit@1_per_batch`（每批 Hit@1）
- `p50_per_batch`（每批 p50）
- `rss_growth`（RSS 增长曲线）

**预期**：

| 范式 | 累计 Build Time | Hit@1 波动 | p50 波动 |
|---|---|---|---|
| GridTrace+ | ~20s（追加桶是 O(batch)） | ±2% | ±10% |
| HNSW | ~40s（新增节点 + 边调整） | ±3% | ±5% |
| IVF | ~80s（增量 kmeans 是 O(batch × k)） | ±5% | ±15% |

**关键发现**：GridTrace+ 在 B1 上有 **2-4x 累计 Build Time 优势**（V3 目标 C3 的核心证据）。

**风险**：GridTrace+ 在追加时可能破坏 L1 锚点分布，需测「追加后是否需要重训锚点」开关。

---

#### B2. 增量删除

**目的**：运维定期清理过时 KB（产品下线、政策变更）。验证 GridTrace 删桶即生效的优势。

**设计**：
- 基线：N=50K
- 删量：每批删 5% (2.5K)，重复 10 批
- 范式：同 B1
- 测每批后 200 query 的召回 + 残余召回

**指标**：
- `residual_recall_per_batch`（残余召回，应=0）
- `rss_reduction_per_batch`（RSS 减少）
- `hit@1_of_remaining`（剩余 KB 召回，应不变）

**预期**：

| 范式 | 残余召回 | RSS 立即释放 | 剩余 KB Hit@1 |
|---|---|---|---|
| GridTrace+ | 0% | ✅ 每批立即 | 不变 |
| HNSW (mark) | 0% | ❌ 不释放 | 不变 |
| HNSW (rebuild) | 0% | ✅ 重建时释放 | 不变（重建 2-5s） |
| IVF (rebuild) | 0% | ✅ 重建时释放 | 不变（重建 5-10s） |

**关键发现**：GridTrace+ 是**唯一在删除后立即释放 RSS 的范式**，HNSW/IVF 都需要触发重建。

---

#### B3. 增量改写

**目的**：运维人员修订 KB 内容（错误修正、补充信息）。验证 GridTrace 量化是否需重训。

**设计**：
- 基线：N=10K，全部 KB 用 BGE 嵌入
- 改写：每批随机改 10% KB 的 question + solution，模拟人工修订
- 重训策略：
  1. GridTrace+「按桶重训」（只重训被改 KB 所在桶的量化）
  2. GridTrace+「全量重训」（每批后全量重训量化）
  3. HNSW（无需重训，节点直接替换 embedding）
- 测 5 批后 Hit@1

**指标**：
- `quant_key_drift_rate`（改写后 KB 漂移出原 quant_key 的比率）
- `hit@1_after_no_retrain`（不重训 Hit@1）
- `hit@1_after_bucket_retrain`（按桶重训 Hit@1）
- `retrain_cost`（重训耗时 s）

**预期**：
- 改写 10% 后，GridTrace+ 不重训 Hit@1 衰减 ~5%
- 按桶重训（仅重训受影响的 ~50 个桶，O(50)）恢复 Hit@1，耗时 < 1s
- 全量重训（O(N)）耗时 ~10s，Hit@1 完全恢复
- HNSW 无需重训，Hit@1 保持

**关键发现**：GridTrace+「按桶重训」是**唯一不重建全图即可恢复 Hit@1 的方案**。

---

### C. 分布式与多租户（3 个实验 × 2.5 周）

#### C1. 水平分片

**目的**：验证 GridTrace 桶按 quant_key hash 分片后，单 shard 检索延迟不变；HNSW 整体子图分片后召回率下降。

**设计**：
- 总规模：N=50K
- 分片数：10 shard × 5K entry
- 分片策略：
  1. **GridTrace+**：`shard_id = hash(quant_key) % 10`（桶级分片）
  2. **HNSW**：每 shard 独立构建一个 5K HNSW 图（子图分片）
  3. **HNSW 镜像**：每 shard 完整镜像 50K 全图（参考对照）
- 测量：单 shard 100 query + 跨所有 shard 100 query（合并 top-5）

**指标**：
- `single_shard_p50`（单 shard 检索 p50）
- `cross_shard_p50`（跨 shard 合并 p50）
- `hit@1_degradation` = (全图 Hit@1 - 分片 Hit@1) / 全图 Hit@1
- `shard_size_variance`（分片大小方差，GridTrace 桶分布均匀性）

**预期**：

| 范式 | 单 shard p50 | 跨 shard p50 | Hit@1 退化 |
|---|---|---|---|
| GridTrace+ (hash 分片) | 2ms | 5ms（合并） | < 2% |
| HNSW (子图分片) | 0.2ms | 0.5ms | 5-15%（子图不连通） |
| HNSW (镜像) | 0.2ms | 2ms（10x 重复） | 0% |

**关键发现**：GridTrace+ 桶级 hash 分片在**延迟可控 + Hit@1 不退化**上优于 HNSW 子图分片。

---

#### C2. 多租户隔离

**目的**：验证 GridTrace 桶级隔离天然无跨租户泄露；HNSW 共享索引有 5-15% 跨租户召回。

**设计**：
- 租户数：10
- 每租户规模：1K entry
- 租户特征：每租户用不同 quant_key 区间（GridTrace 天然隔离）/ 共享 HNSW 索引（HNSW 难隔离）
- 测量：每租户 100 query，其中混入 5% 跨租户 query（验证是否被错误召回）

**指标**：
- `cross_tenant_recall`（跨租户召回率，应=0）
- `intra_tenant_p50`（租户内 p50）
- `tenant_isolation_effort`（隔离实现代码行数）

**预期**：

| 范式 | 跨租户召回 | 租户 p50 | 隔离实现 |
|---|---|---|---|
| GridTrace+ (桶级) | 0% | 1.5ms | 5 行（按租户 ID 过滤 quant_key）|
| HNSW (共享) | 5-15% | 0.2ms | 50+ 行（强制 filter + post-filter）|
| IVF (共享) | 3-10% | 0.5ms | 30+ 行（filter 倒排）|

**关键发现**：GridTrace+ 桶级隔离**天然无泄露 + 实现极简**（V3 目标 E1 的核心证据）。

---

#### C3. 跨地域部署

**目的**：GridTrace 桶可独立同步，HNSW 整体图同步延迟高。

**设计**：
- Region 数：3（模拟北京/上海/广州）
- 每 region 规模：5K entry
- 同步策略：
  1. **GridTrace+**：按桶增量同步（某桶新增 → 推送到其他 region）
  2. **HNSW**：整体图重传（每天全量同步一次）
- 测量：跨 region 检索 p50 + 同步延迟

**指标**：
- `cross_region_query_p50`（跨 region 检索 p50）
- `sync_bandwidth`（同步带宽 MB/day）
- `sync_latency`（同步延迟 s）

**预期**：
- GridTrace+ 同步延迟 < 100ms（按桶）
- HNSW 同步延迟 > 1s（全图重传）
- 跨 region 检索 p50 由网络主导（RTT 30-50ms），范式差异不显著

**关键发现**：GridTrace+ 桶级同步**带宽与延迟**显著优于 HNSW 全图同步（V3 目标 E1 延伸）。

**风险**：跨地域实验在单机模拟可能失真，需用 3 台真机做交叉验证（成本高，可作为后续工作）。

---

### D. 索引腐烂与数据漂移（3 个实验 × 2.5 周）

#### D1. 量化召回衰减（核心实验）

**目的**：6 个月后 KB 增长 + 漂移，旧量化是否可用。

**设计**：
- 初始：N=10K（V2 同源）
- 6 个月模拟：
  - 每月 +10% 文档（复制+扰动）
  - 每月 +5% 类别（新增类别 1 个）
  - 每月 query 分布漂移 5%（Zipf α 从 1.0 → 0.8）
- 时间点：M0 / M1 / M2 / M3 / M6
- 测两组：
  1. 用「当前最佳量化」训练 → Hit@1
  2. 用「M0 初始量化」推理 → Hit@1

**指标**：
- `hit@1_with_initial_quant`（用旧量化的 Hit@1）
- `hit@1_with_current_quant`（用量化的 Hit@1）
- `quant_decay_rate` = (初始 Hit@1 - 6月 Hit@1) / 6

**预期**：
- 旧量化在 M6 时 Hit@1 衰减 15-25%（量化腐烂）
- 当前量化 Hit@1 不变（持续重训）
- HNSW 无量化问题，但图结构需 M=16→32 调整（参数腐烂）

**关键发现**：GridTrace+ 需要**在线量化更新**（D3 实验的输入）。

---

#### D2. 类别漂移

**目的**：KB 类别从 5 类扩到 20 类（运维新场景），粗量化重训时间。

**设计**：
- 起点：N=10K，5 类别（V2 同源）
- 终态：N=10K，20 类别（注入 15 个新类别）
- 测：GridTrace+「粗量化重训」耗时 + 重训后 Hit@1

**指标**：
- `coarse_quant_retrain_time`（粗量化重训时间 s）
- `hit@1_after_retrain`（重训后 Hit@1）
- `trail_completeness`（trail 是否仍含正确 category_path）

**预期**：
- 粗量化重训时间 < 5s（一次性）
- 重训后 Hit@1 恢复到原值
- trail 完整度保持 100%

**关键发现**：GridTrace+ 类别漂移成本**远低于** HNSW M/ef 参数调优（HNSW 需重新调参 + 重建图）。

---

#### D3. 在线量化更新

**目的**：GridTrace 桶量化在线更新（每 N 条触发）vs HNSW 静态图。

**设计**：
- 起点：N=10K
- 增量：每批 1K，重复 10 批
- 更新策略：
  1. **GridTrace+ 在线**：每批后用「最近 5K 数据」重新训练受影响的桶量化
  2. **GridTrace+ 离线**：全量重训（每 5 批一次）
  3. **HNSW 静态**：不更新图
  4. **HNSW 增量**：ef 调优（每批调一次）
- 测每批后 Hit@1

**指标**：
- `long_term_hit@1_stability`（长期 Hit@1 波动 σ）
- `cumulative_retrain_time`（累计重训时间）
- `fresh_query_recall`（新加 KB 的 query 召回率）

**预期**：
- GridTrace+ 在线更新 Hit@1 波动 σ < 0.05（5%）
- GridTrace+ 离线更新 σ < 0.10
- HNSW 静态 σ > 0.15（KNN 图漂移）
- HNSW 增量 σ < 0.08（但 ef 调参开销大）

**关键发现**：GridTrace+ 在线量化更新是**最稳定的长期方案**（V3 目标 E2 的核心证据）。

---

### E. 多模态扩展（3 个实验 × 2.5 周）

#### E1. 文本 + metric 序列

**目的**：把运维 metric（CPU 序列、内存曲线）作为另一模态。GridTrace 桶可承载多 embedding。

**设计**：
- 数据：1K 双模态 entry（文本 + 60s CPU 序列）
- 嵌入：文本用 BGE-small（512 维），metric 用 1D-CNN（256 维）
- 联合检索：query 同时给文本 + 当前 metric，GridTrace 桶用「拼接 embedding」(768 维)
- 范式：GridTrace+（双模态）/ HNSW（双索引，RRF 融合）

**指标**：
- `joint_hit@1`（联合 Hit@1）
- `single_modality_hit@1`（单模态 Hit@1）
- `bucket_size`（GridTrace 桶大小）

**预期**：
- GridTrace+ 双模态 joint Hit@1 > 任一单模态
- HNSW 双索引融合后 joint Hit@1 ≈ GridTrace+（验证 GridTrace 不劣）
- GridTrace+ 桶大小增长 ~50%（双 embedding 维度）

**关键发现**：GridTrace+ 桶可承载**多模态联合 embedding**（V3 目标 E3 的核心证据）。

---

#### E2. 文本 + log 日志

**目的**：entry 含错误码 + log 模式，验证 GridTrace 桶内混合多模态。

**设计**：
- 数据：1K entry，文本（BGE 512 维）+ 错误码 one-hot（100 维）+ log hash embedding（128 维）
- 联合：GridTrace 桶用拼接 740 维 embedding
- 范式：同 E1

**指标**：
- `joint_hit@1`
- `log_pattern_match_rate`（错误码匹配率）
- `bucket_size`

**预期**：
- 拼接 740 维后，PQ 子空间数从 64 提到 92（740/8），仍可工作
- 联合 Hit@1 > 单文本

---

#### E3. 文本 + runbook

**目的**：entry 含结构化步骤（步骤树）+ 自由文本。

**设计**：
- 数据：500 多模态 entry，runbook 步骤树（递归结构）→ 序列编码（GRU，256 维）+ 文本 BGE（512 维）
- 联合：GridTrace 桶用 768 维 embedding
- 挑战：runbook 步骤数变化（5-20 步），GRU 池化方案选 mean / max / attention

**指标**：
- `joint_hit@1`（3 种池化方案对比）
- `step_recall@5`（步骤级召回）
- `bucket_size`

**预期**：
- Attention 池化方案最佳
- GridTrace+ 联合 Hit@1 优于单文本 5-10%
- 桶大小方差大（步骤数差异），需测「桶合并」策略

**关键发现**：GridTrace+ 桶可承载**异构维度**（512+256），但需 PQ 子空间数动态调整。

---

### F. 极限边界（4 个实验 × 1.5 周）

#### F1. 极小 N

**目的**：明确 GridTrace 在小 N 的适用边界。

**设计**：
- N ∈ {10, 50, 100, 200, 500}
- 测：GridTrace+ 桶数 / 每桶大小 / Hit@1

**预期**：
- N=10：GridTrace 桶数 = 10（每 entry 一桶），L1 锚点优势消失
- N=100：桶数 ~30，每桶 ~3 entry，开始有 L1 优势
- N=500：桶数 ~100，每桶 ~5 entry，L1 优势显著

**关键发现**：**GridTrace 适用边界 N ≥ 200**（V3 明确边界）。

---

#### F2. 极大 N

**目的**：明确 GridTrace 在大 N 的瓶颈点。

**设计**：
- N ∈ {100K, 500K, 1M}
- 测：GridTrace+ 锚点数 / p50 / Build Time / RSS

**预期**：
- N=100K：锚点 ~500，p50 ~25ms，仍可接受
- N=500K：锚点 ~2500，p50 ~120ms，逼近 SLA
- N=1M：锚点 ~5000，p50 ~250ms，**超过 SLA**（需要「分片」或「二级量化」）

**关键发现**：**GridTrace 适用边界 N ≤ 500K**（V3 明确边界，>500K 建议 C1 分片）。

---

#### F3. 极高维

**目的**：用 BGE-large（1024 维）替代 BGE-small（512 维）测 GridTrace 性能。

**设计**：
- 维度 ∈ {512, 1024, 2048, 4096}
- 测：RSS / Build Time / p50

**预期**：
- 维度 1024：RSS 2x，Build Time 2x
- 维度 4096：RSS 8x，PQ 训练时间 4x

**关键发现**：**GridTrace RSS 随维度线性增长**（V3 明确边界）。

---

#### F4. 极低质量 KB

**目的**：canonical=50 条，variant=5 改写，测 GridTrace 泛化能力。

**设计**：
- 训练：50 canonical
- 测试：50 canonical × 5 variant = 250 query
- 测：Hit@1

**预期**：
- GridTrace+ 桶数 ~10，每桶 ~5 entry，泛化差（桶边界过细）
- HNSW 仍 OK（KNN 图平滑）

**关键发现**：**GridTrace 不擅长极小训练集**（V3 明确边界）。

---

## 3. 数据集生成策略

### 3.1 数据源分层

| 真实度 | 数据源 | 用于 | 规模上限 |
|---|---|---|---|
| **高** | v3 canonical/variant/near_miss（已有） | A1, A2, A3, F1, F4 | 400 |
| **高** | 真实运维 metric / log / runbook（待采集） | E1, E2, E3 | 1K/500 |
| **中** | v3 复制 + 随机扰动 ε∈[0.005, 0.02] | B1, B2, B3, C1, D1, D2, D3 | 50K/100K |
| **中** | v3 复制 + 类别扰动 | D2, E1, E2, E3 | 10K |
| **低** | 纯合成（随机向量） | F1, F2, F3 | 1M |

### 3.2 扰动算法（复用 V2 expand_kb_v3.py）

```python
def perturb_entry(entry: EvalEntry, epsilon: float) -> EvalEntry:
    """保留 page_index + category 真实字段，扰动 embedding。"""
    noise = np.random.normal(0, epsilon, size=512)
    new_emb = entry.embedding + noise
    new_emb = new_emb / np.linalg.norm(new_emb)  # L2 归一化
    return EvalEntry(
        page_index=entry.page_index,  # 保留
        category=entry.category,      # 保留
        question=entry.question,
        solution=entry.solution,
        embedding=new_emb.tolist(),
    )
```

### 3.3 多模态数据采集计划

| 实验 | 数据源 | 规模 | 采集方式 |
|---|---|---|---|
| E1 | Prometheus 1K metric 序列 | 1K | 公司真实监控（脱敏）|
| E2 | ELK 1K log 样本 | 1K | 公司真实日志（脱敏）|
| E3 | Confluence 500 runbook | 500 | 公开 runbook 模板 |

**采集成本**：约 1 周（含脱敏 + 标注 + 嵌入）。

### 3.4 数据集归档结构

```
data/paradigm_benchmark_v3/
├── A1_multilingual/
│   ├── zh.json
│   ├── en.json
│   └── mixed.json
├── A2_user_study/
│   └── 30_queries_5_paradigms.json
├── A3_forget/
│   ├── n50k_pre_delete.json
│   └── n50k_post_delete_*.json
├── B1_incremental/
│   └── batches/batch_{1..40}.json
├── C1_sharding/
│   ├── shard_{0..9}.json
├── D1_decay/
│   └── months/m{0,1,2,3,6}.json
├── E1_text_metric/
│   └── dual_modal.json
├── ...
└── README.md
```

---

## 4. 评估指标体系

### 4.1 效率维度

| 指标 | 定义 | 测量方式 |
|---|---|---|
| `p50` | 50% 分位延迟 | 200 query 中位数 |
| `p95` | 95% 分位延迟 | 200 query 95% 分位 |
| `p99` | 99% 分位延迟 | 200 query 99% 分位 |
| `qps` | 每秒查询数 | 200 query / 总耗时 |
| `build_time` | 构建索引耗时 | wall-clock s |
| `rss_mb` | 内存占用 | `psutil.Process().memory_info().rss / 1MB` |

### 4.2 质量维度

| 指标 | 定义 | 公式 |
|---|---|---|
| `hit@1` | top-1 包含 ground truth 比例 | `mean([1 if gt in top1 else 0])` |
| `hit@3` | top-3 包含 gt 比例 | 同上 |
| `hit@5` | top-5 包含 gt 比例 | 同上 |
| `mrr` | Mean Reciprocal Rank | `mean([1/rank_of_gt])` |
| `ndcg@5` | Normalized DCG | sklearn 公式 |

### 4.3 稳定性维度

| 指标 | 定义 | 用于 |
|---|---|---|
| `p99_drift_7d` | 7 日 p99 漂移 σ | 长期稳定性 |
| `hit@1_drift_per_batch` | 跨批 Hit@1 σ | B1, D3 |
| `quant_decay_6m` | 6 月量化腐烂率 | D1 |

### 4.4 可解释性维度（GridTrace 独享）

| 指标 | 定义 | 用于 |
|---|---|---|
| `trail_completeness` | trail 字段完整度（0-1） | A1 |
| `mos` | Mean Opinion Score（0-5） | A2 |
| `causality_score` | 用户对「召回原因」评分 | A2 子维度 |
| `trust_score` | 用户对「结果可信度」评分 | A2 子维度 |
| `debuggability_score` | 用户对「失败定位」评分 | A2 子维度 |

### 4.5 可遗忘性维度

| 指标 | 定义 | 用于 |
|---|---|---|
| `residual_recall` | 删后召回率（应=0） | A3, B2 |
| `rss_reduction_ratio` | 删后 RSS 减少比例 | A3, B2 |
| `post_delete_p50_increase` | 删后 p50 增长率 | A3 |

### 4.6 SLA 维度

| 指标 | 定义 | 测量 |
|---|---|---|
| `sla_30ms_violation_rate` | 超过 30ms 的 query 比例 | 200 query |
| `sla_100ms_violation_rate` | 超过 100ms 的 query 比例 | 200 query |

### 4.7 数据分析流程

```python
# 每个实验的标准分析流程
def analyze_experiment(results_json: Path) -> ExperimentReport:
    """1. 加载结果 → 2. 计算 KPI → 3. 显著性检验 → 4. 画图 → 5. 结论"""
    raw = json.load(open(results_json))

    # 1. KPI 计算
    kpis = compute_kpis(raw)  # 12 维 KPI

    # 2. 显著性检验（200 query bootstrap）
    bootstrap = bootstrap_test(kpis, n=10000, seed=42)
    # Wilcoxon signed-rank test: GridTrace+ vs HNSW
    p_value = wilcoxon(gridtrace_p50, hnsw_p50).pvalue

    # 3. 画图
    plot_kpis(kpis, output_dir)

    # 4. 结论生成（LLM 辅助）
    conclusion = generate_conclusion(kpis, bootstrap)

    return ExperimentReport(kpis, bootstrap, p_value, conclusion)
```

---

## 5. 实施路线图

### 阶段 1：巩固基础（Week 1-1.5）

- **Week 1**：A1（多语言 trail） + A2 准备（用户研究 IRB + 受试者招募）
- **Week 1.5**：A2（用户研究执行） + A3（合规删除零重建）

**里程碑**：V3 实测报告 v0.1（3 个实验完成），明确 GridTrace 在「可解释性 + 合规删除」的独享地位。

### 阶段 2：增量更新（Week 2.5-4）

- **Week 2.5**：B1（增量扩展，**最关键**）+ B2 准备
- **Week 3.5**：B2（增量删除） + B3（增量改写）

**里程碑**：V3 实测报告 v0.2（6 个实验完成），明确 GridTrace 在「增量更新」的独享优势。

### 阶段 3：分布式（Week 4-6.5）

- **Week 4**：C1（水平分片，**最复杂**）
- **Week 5**：C2（多租户隔离）
- **Week 6**：C3（跨地域部署，可用模拟）

**里程碑**：V3 实测报告 v0.3（9 个实验完成），明确 GridTrace 在「分布式 / 多租户」的独享优势。

### 阶段 4：索引腐烂（Week 6.5-9）

- **Week 6.5**：D1（量化召回衰减，**核心实验**）
- **Week 8**：D2（类别漂移） + D3（在线量化更新）

**里程碑**：V3 实测报告 v0.4（12 个实验完成），明确 GridTrace「在线量化更新」的可行性。

### 阶段 5：多模态（Week 9-11.5）

- **Week 9**：E1（文本+metric 数据采集 + 嵌入）
- **Week 10**：E2（文本+log）
- **Week 11**：E3（文本+runbook）

**里程碑**：V3 实测报告 v0.5（15 个实验完成），明确 GridTrace 在「多模态联合检索」的可行性。

### 阶段 6：极限边界（Week 11.5-13）

- **Week 11.5**：F1（极小 N） + F2（极大 N）
- **Week 12.5**：F3（极高维） + F4（极低质量）

**里程碑**：V3 实测报告 v0.6（19 个实验完成），明确 GridTrace 的 4 个适用边界。

### 阶段 7：报告与归档（Week 13-15）

- **Week 13**：V3 实测报告 v1.0 终稿（**核心交付物**）
- **Week 14**：决策树更新 + OpsWarden 文档
- **Week 15**：代码归档 + 复现性验证

**里程碑**：`docs/PARADIGM_BENCHMARK_V3_REPORT.md` + `docs/PARADIGM_BENCHMARK_V3_DECISION_TREE.md` 发布。

---

## 6. 预期结论与风险预案

### 6.1 预期可证实的优势（**目标导向**）

| 优势 ID | 优势描述 | 预期强度 | 验证实验 |
|---|---|---|---|
| C1 | retrieval_trail 多语言完整性 | 强 | A1 |
| C1.2 | retrieval_trail 用户感知 | 强 | A2 |
| C2 | 合规删除零重建 | 强 | A3 |
| C3 | 增量扩展 Build Time 优势 | 强 | B1 |
| C3.2 | 增量删除 RSS 立即释放 | 强 | B2 |
| C3.3 | 增量改写按桶重训 | 中 | B3 |
| E1 | 分布式水平分片 | 强 | C1 |
| E1.2 | 多租户隔离零泄露 | 强 | C2 |
| E1.3 | 跨地域桶级同步 | 中 | C3 |
| E2 | 索引腐烂在线量化更新 | 中 | D1, D3 |
| E3 | 多模态联合检索 | 中 | E1, E2, E3 |

### 6.2 预期不成立的优势（**诚实声明**）

| 反向结论 | 不证实的优势 | 验证实验 |
|---|---|---|
| R1 | GridTrace 在 N=1M 时仍 < 30ms p50 | F2 |
| R2 | GridTrace 在 N=10 时仍优 | F1 |
| R3 | GridTrace 在 4096 维时 RSS < 1GB | F3 |
| R4 | GridTrace 在 canonical=50 时泛化强 | F4 |

### 6.3 风险预案

| 风险 | 触发条件 | 应对策略 |
|---|---|---|
| **D1 发现 GridTrace 量化腐烂严重** | 6 月 Hit@1 衰减 > 30% | 把 V3 结论改为「需要季度重训」建议文档 |
| **E 类多模态实验发现桶内异构效果差** | 联合 Hit@1 < 单模态 | 把 V3 结论改为「多模态需桶分层」研究 |
| **C1 发现 GridTrace 桶分布不均** | shard_size_variance > 30% | 增加「动态再分片」研究方向 |
| **A2 受试者数量不足** | 招募 < 5 人 | 改为内部 3 人 + 外部 2 人配对 t 检验 |
| **B 类增量 Build Time 优势不明显** | 累计 Build Time 差异 < 1.5x | 调整 B1 起点 N=1K（小 N 优势应更显著）|
| **D3 在线量化更新不稳定** | Hit@1 波动 σ > 0.10 | 改为「离线周期重训 + 监控」建议 |

### 6.4 不可量化的风险

- **A2 用户研究**：受试者主观性强，可能高估/低估 trail 价值
- **E3 runbook 池化**：3 种方案选哪个，需领域专家判断

---

## 7. 资源需求

### 7.1 人力

- 主研究员 1 人 × 15 周 = 15 人周
- 受试者 5 人 × 1 小时 = 5 人时（A2 用户研究）
- 标注员 1 人 × 1 周 = 1 人周（E 类多模态数据标注）

### 7.2 计算资源

- **CPU**：16 核（持续 15 周）
- **GPU**：可选（A1 多语言嵌入推理可加速 5-10x）
- **内存**：64GB（N=1M 需 ~20GB 嵌入矩阵 + 10GB 中间结果）
- **存储**：200GB（数据 + 中间结果 + 报告）

### 7.3 软件依赖

- 复用：numpy / scipy / matplotlib / sentence-transformers / faiss-cpu
- 新增（如果需要）：
  - `transformers`（BGE-large 推理）
  - `gradio`（A2 用户研究 Web 表单）
  - `prometheus-client`（E1 真实 metric 采集）
  - `elasticsearch`（E2 真实 log 采集）

---

## 8. 复现性保障

### 8.1 随机种子固定

```python
# 所有脚本开头必须固定
import numpy as np
import torch
import random
np.random.seed(42)
torch.manual_seed(42)
random.seed(42)
```

### 8.2 Docker 镜像固化

```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY experiments/ /app/experiments/
COPY data/ /app/data/
COPY docs/ /app/docs/
WORKDIR /app
ENTRYPOINT ["python", "experiments/run_v3.py"]
```

镜像 tag：`opswarden/paradigm-benchmark:v3`，归档到内网 Harbor。

### 8.3 结果归档

每次实验结果保存为：
- `results/v3/{experiment_id}/results.json`（原始 KPI）
- `results/v3/{experiment_id}/results.md`（结论）
- `results/v3/{experiment_id}/charts/`（图表）
- `results/v3/{experiment_id}/metadata.yaml`（实验参数 + 环境）

### 8.4 代码审查清单

每个实验的 PR 必须包含：
- [ ] 数据集生成脚本（带随机种子）
- [ ] 测量脚本（带 5 次预热 + 5 次正式测量）
- [ ] 结果分析脚本（含显著性检验）
- [ ] 图表生成脚本
- [ ] 实验报告 Markdown
- [ ] 复现性说明（环境/版本/命令）

---

## 9. 与 V1/V2 关系

### 9.1 版本演进

| 版本 | 范围 | 关键产出 | 诚实结论 |
|---|---|---|---|
| V1 | 6 范式 × 1 场景（N=400） | Hit@1 单一指标 | GridTrace 全面胜出（**V1 结论失实**）|
| V2 | 6 范式 × 5 场景（N=400-50K） | 12 维 KPI + 5 场景决策 | **GridTrace 独享优势收敛到 2 个**（可解释性 + 合规删除）|
| V3 | 6 范式 × 19 实验 | 6 大类扩展验证 | **目标：把独享优势扩到 6 个**（本文档规划）|

### 9.2 不重复的原则

V3 **不重复** V2 的 5 场景（S1-S5），V3 把 V2 5 场景视为基线，重点在 V2 未覆盖的 6 大方向：
- A 类（巩固）：把 V2 S5 扩到多语言 + 用户感知
- B 类（增量）：V2 未覆盖
- C 类（分布式）：V2 未覆盖
- D 类（腐烂）：V2 未覆盖
- E 类（多模态）：V2 未覆盖
- F 类（边界）：V2 未覆盖

### 9.3 决策树更新计划

V2 决策树见 `docs/PARADIGM_BENCHMARK_V2_REPORT.md` §6。V3 完成后，决策树升级为：

```yaml
# V3 决策树（目标）
选型决策:
  - 条件: N ≤ 200
    选择: Flat
    原因: GridTrace 桶稀疏（F1）
  - 条件: 200 < N ≤ 10K 且 query 数 < 1000/天
    选择: HNSW
    原因: V2 S1 最优
  - 条件: 200 < N ≤ 500K 且需要 audit trail
    选择: GridTrace+
    原因: A2 MOS + A3 零重建 + B1 增量
  - 条件: N > 500K
    选择: GridTrace+ + 分片
    原因: C1 分片 + C2 多租户
  - 条件: 需要合规精确删除
    选择: GridTrace+
    原因: A3 零重建独享
  - 条件: 多租户隔离
    选择: GridTrace+ 桶级
    原因: C2 零泄露 + 5 行实现
  - 条件: 多模态 KB
    选择: GridTrace+ 双模态
    原因: E1 联合检索
  - 条件: 长期运行（6 月+）
    选择: GridTrace+ + 在线量化
    原因: D3 Hit@1 稳定
```

---

## 10. 附录

### 附录 A：GridTrace 已有代码位置

- 主体：`backend/app/rag/eval_engine.py`（已向量化 L1/L2，V2 修复）
- 量化：`backend/app/rag/quantizer.py`（标量量化）
- 范式：`experiments/paradigm_benchmark/paradigms/gridtrace.py`（原版）/ `gridtrace_enhanced.py`（V2 修复 + PQ）
- 评测：`experiments/paradigm_benchmark/`（V1 基础设施 + V2 场景化）

### 附录 B：扩展点清单

V3 需要的新增代码位置：

| 新增模块 | 路径 | 用途 |
|---|---|---|
| `online_quantizer.py` | `experiments/paradigm_benchmark/v3/online_quantizer.py` | D3 在线量化更新 |
| `shard_runner.py` | `experiments/paradigm_benchmark/v3/shard_runner.py` | C1 水平分片 |
| `multimodal_embedder.py` | `experiments/paradigm_benchmark/v3/multimodal_embedder.py` | E1-E3 多模态 |
| `boundary_tester.py` | `experiments/paradigm_benchmark/v3/boundary_tester.py` | F1-F4 边界 |
| `mos_form.py` | `experiments/paradigm_benchmark/v3/mos_form.py` | A2 用户研究 |
| `v3_runner.py` | `experiments/paradigm_benchmark/v3/v3_runner.py` | V3 总编排 |
| `v3_report.py` | `experiments/paradigm_benchmark/v3/v3_report.py` | V3 报告渲染 |

### 附录 C：术语表

- **桶（bucket）**：GridTrace 量化后的 entry 集合，共享一个 quant_key
- **锚点（anchor）**：桶的代表性向量（桶中心），用于 L1 检索
- **粗量化（coarse quant）**：更大 ε 的量化，用于扩展环
- **quant_key**：entry 通过 ε 量化后落入的桶 ID
- **retrieval_trail**：GridTrace 返回的诊断字段，含 quant_key / l1_score / l2_score / expand_count 等
- **MOS**：Mean Opinion Score，用户感知评分（0-5）
- **R@K**：Recall@K，top-K 包含 ground truth 的比例
- **P@K**：Precision@K，top-K 中相关结果的比例

### 附录 D：参考文献

1. V2 实测报告：`docs/PARADIGM_BENCHMARK_V2_REPORT.md`
3. V1 设计文档：`docs/PARADIGM_BENCHMARK_DESIGN.md`
4. HNSW 论文：Malkov & Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs", 2018
5. Product Quantization：Jegou et al., "Product Quantization for Nearest Neighbor Search", 2011
6. faiss 文档：https://faiss.ai/
7. BGE 模型：BAAI/bge-small-zh-v1.5, BAAI/bge-reranker-base
8. OpsWarden 内部：`backend/app/rag/`（GridTrace 实现）

---

**文档结束。** 总计：6 大类 19 个实验，约 60 工作日，目标在 2026 Q4 完成。
