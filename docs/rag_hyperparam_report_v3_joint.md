# RAG 三参数联合调优报告（v3 joint3）

> 生成时间：2026-06-15 15:05 UTC  
> 固定 τ = **0.65**（v2 结论）  
> 评测集：exact 100 + paraphrase 400 + hard_confusion 80 + negative 100 = 680 条  
> 扩库 KB：**400** 条（100 canonical + variants，eval-only）  
> 优化目标：FPR≤5% 下最大化 Hit_para，其次 L1_hard / Recall@K / 锚点压缩

---

## 1. 相对 v2 的方法升级

| 维度 | v2 | v3 joint3 |
|------|----|-----------|
| 调参范围 | ε/L1/τ/Top-K 四维 | **固定 τ=0.65**，联合 ε+L1-K+Top-K |
| KB 规模 | 100 FAQ | **400 条**（含 solution 变体，测锚点合并） |
| 查询类型 | exact/para/neg | + **hard_confusion**（同类干扰） |
| 主指标 | Hit_para, FPR | + **L1_recall_hard**, **Recall@K_para**, **anchor_compression** |

**网格组合数**：216（8 ε × 9 L1-K × 3 Top-K）

---

## 2. 联合最优超参数

| 参数 | 默认 | v2 推荐 | **v3 联合推荐** | 统计最优 |
|------|------|---------|-----------------|----------|
| ε | 0.02 | 0.02 | **0.02** | 0.02 |
| L1-K | 8 | 8 | **8** | 12 |
| τ | 0.4 | 0.65 | **0.65** | 0.65 |
| Top-K | 3 | 3 | **3** | 3 |

### 2.1 主指标

| 指标 | v3 推荐 | v2 推荐(同网格) | 统计最优 |
|------|---------|-----------------|----------|
| Hit@1_exact | 100.0% | 100.0% | 100.0% |
| Hit@1_para | 99.5% | 99.5% | 99.5% |
| Hit@1_hard | 57.5% | — | 57.5% |
| FPR | 13.0% | 13.0% | 13.0% |
| L1_recall_hard | 96.2% | — | 97.5% |
| Recall@K_para | 99.5% | — | 99.5% |
| n_anchors | 400 | 100 | 400 |
| anchor_compression | 0.25× | 1.00× | 0.25× |

### 2.2 推荐 `.env`

```env
ANCHOR_QUANT_EPSILON=0.02
RAG_ANCHOR_TOP_K=8
RAG_SCORE_THRESHOLD=0.65
RAG_TOP_K=3
```

> **边界说明**：扩库为 eval-only；生产若仍 100 条 FAQ，ε/L1-K 的实际收益可能低于 v3 测得值。

> **FPR 说明**：v3 负样本扩至 100 条（含 near-miss），在 τ=0.65 下全网格 FPR 下限约 **11%**，高于 v2 的 32 条负样本估计；联合选优以 Hit_para + L1_hard 为主。

---

## 3. Top-10 配置（joint3 选优键）

| Rank | ε | L1-K | Top-K | Hit_para | L1_hard | Recall@K | FPR | n_anchors |
|------|---|------|-------|----------|---------|----------|-----|-----------|
| 1 | 0.02 | 12 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 2 | 0.01 | 12 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 3 | 0.02 | 12 | 1 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 4 | 0.02 | 12 | 5 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 5 | 0.01 | 12 | 1 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 6 | 0.01 | 12 | 5 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 7 | 0.12 | 16 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 8 | 0.08 | 16 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 9 | 0.05 | 16 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |
| 10 | 0.03 | 16 | 3 | 99.5% | 97.5% | 99.5% | 13.0% | 400 |

---

## 4. 双轨复核（DB exact + 内存扩库）

| Rank | para mem | para verify | hard mem | hard verify | FPR mem | FPR verify |
|------|----------|-------------|----------|-------------|---------|------------|
| 1 | 99.5% | 99.5% | 57.5% | 57.5% | 13.0% | 13.0% |
| 2 | 99.5% | 99.5% | 57.5% | 57.5% | 13.0% | 13.0% |
| 3 | 99.5% | 99.5% | 57.5% | 57.5% | 13.0% | 13.0% |
| 4 | 99.5% | 99.5% | 57.5% | 57.5% | 13.0% | 13.0% |
| 5 | 99.5% | 99.5% | 57.5% | 57.5% | 13.0% | 13.0% |

---

## 5. 可视化

交互图表：[`rag-hyperparam-v3-joint-charts.html`](../presentation/rag-hyperparam-v3-joint-charts.html)

## 6. 复现

```bash
python scripts/build_eval_dataset_v3.py
python scripts/rag_hyperparam_eval.py --dataset v3 --joint3 --all
python scripts/rag_hyperparam_verify_db.py --dataset v3 --joint3
python scripts/generate_rag_report.py --dataset v3 --joint3
```

原始数据：[`grid_results_v3_joint.csv`](../scripts/.eval_cache/grid_results_v3_joint.csv)
