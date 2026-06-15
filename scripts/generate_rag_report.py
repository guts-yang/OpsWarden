#!/usr/bin/env python3
"""Generate RAG hyperparameter tuning report from grid + DB verify results.

Usage (from repo root):
    python scripts/generate_rag_report.py --dataset v2
    python scripts/generate_rag_report.py --dataset v3 --joint3
    python scripts/generate_rag_report.py --dataset v1
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CACHE_DIR = SCRIPTS / ".eval_cache"
DOCS_DIR = ROOT / "docs"
BASELINE = {"epsilon": 0.02, "anchor_k": 8, "threshold": 0.40, "top_k": 3}
V2_REC = {"epsilon": 0.02, "anchor_k": 8, "threshold": 0.65, "top_k": 3}
FIXED_TAU_V3 = 0.65
FPR_MAX = 0.05


def paths_for(version: str) -> dict[str, Path]:
    if version == "v3":
        return {
            "grid": CACHE_DIR / "grid_results_v3_joint.csv",
            "top5": CACHE_DIR / "top5_configs_v3_joint.json",
            "verify": CACHE_DIR / "db_verify_results_v3_joint.json",
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v3.json",
            "report": DOCS_DIR / "rag_hyperparam_report_v3_joint.md",
            "charts": ROOT / "presentation" / "rag-hyperparam-v3-joint-charts.html",
        }
    if version == "v2":
        return {
            "grid": CACHE_DIR / "grid_results_v2.csv",
            "top5": CACHE_DIR / "top5_configs_v2.json",
            "verify": CACHE_DIR / "db_verify_results_v2.json",
            "dataset": SCRIPTS / "eval_datasets" / "faq_eval_v2.json",
            "report": DOCS_DIR / "rag_hyperparam_report.md",
        }
    return {
        "grid": CACHE_DIR / "grid_results.csv",
        "top5": CACHE_DIR / "top5_configs.json",
        "verify": CACHE_DIR / "db_verify_results.json",
        "dataset": SCRIPTS / "eval_datasets" / "faq_exact.json",
        "report": DOCS_DIR / "rag_hyperparam_report.md",
    }


def load_grid(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (centre - margin) / denom), min(1.0, (centre + margin) / denom)


def config_sort_key_v3_joint(row: dict, fpr_max: float) -> tuple:
    fpr = float(row["fpr"])
    return (
        1 if fpr <= fpr_max + 1e-9 else 0,
        float(row["hit1_para"]),
        float(row["l1_recall_hard"]),
        float(row["recall_at_k_para"]),
        float(row["anchor_compression"]),
        -int(row["anchor_k"]),
        -abs(int(row["top_k"]) - 3),
        float(row["epsilon"]),
    )


def find_config(rows: list[dict], cfg: dict) -> dict | None:
    for row in rows:
        if (
            abs(float(row["epsilon"]) - cfg["epsilon"]) < 1e-9
            and int(row["anchor_k"]) == cfg["anchor_k"]
            and abs(float(row["threshold"]) - cfg["threshold"]) < 1e-9
            and int(row["top_k"]) == cfg["top_k"]
        ):
            return row
    return None


def slice_at_tau(rows: list[dict], *, epsilon: float, anchor_k: int, top_k: int, threshold: float) -> dict | None:
    for row in rows:
        if (
            abs(float(row["epsilon"]) - epsilon) < 1e-9
            and int(row["anchor_k"]) == anchor_k
            and int(row["top_k"]) == top_k
            and abs(float(row["threshold"]) - threshold) < 1e-9
        ):
            return row
    return None


def generate_v3_charts_html(p: dict[str, Path], rows: list[dict], rec: dict) -> None:
    """Build interactive charts HTML from grid CSV aggregates."""
    tau = FIXED_TAU_V3
    top_k_ref = 3
    ak_ref = int(rec["anchor_k"])

    epsilons = sorted({float(r["epsilon"]) for r in rows})
    anchor_ks = sorted({int(r["anchor_k"]) for r in rows})
    top_ks = sorted({int(r["top_k"]) for r in rows})

    eps_hit = []
    eps_anchors = []
    for e in epsilons:
        row = slice_at_tau(rows, epsilon=e, anchor_k=ak_ref, top_k=top_k_ref, threshold=tau)
        if row:
            eps_hit.append(round(float(row["hit1_para"]) * 100, 1))
            eps_anchors.append(int(row["n_anchors"]))
        else:
            eps_hit.append(0)
            eps_anchors.append(0)

    ak_hard = []
    ak_hit = []
    for ak in anchor_ks:
        row = slice_at_tau(rows, epsilon=float(rec["epsilon"]), anchor_k=ak, top_k=top_k_ref, threshold=tau)
        if row:
            ak_hard.append(round(float(row["l1_recall_hard"]) * 100, 1))
            ak_hit.append(round(float(row["hit1_para"]) * 100, 1))
        else:
            ak_hard.append(0)
            ak_hit.append(0)

    tk_recall = []
    tk_hit = []
    for tk in top_ks:
        row = slice_at_tau(rows, epsilon=float(rec["epsilon"]), anchor_k=ak_ref, top_k=tk, threshold=tau)
        if row:
            tk_recall.append(round(float(row["recall_at_k_para"]) * 100, 1))
            tk_hit.append(round(float(row["hit1_para"]) * 100, 1))
        else:
            tk_recall.append(0)
            tk_hit.append(0)

    heat_eps = epsilons
    heat_ak = anchor_ks
    heat_matrix: list[list[float]] = []
    for ak in heat_ak:
        row_vals = []
        for e in heat_eps:
            row = slice_at_tau(rows, epsilon=e, anchor_k=ak, top_k=top_k_ref, threshold=tau)
            row_vals.append(round(float(row["hit1_para"]) * 100, 1) if row else 0)
        heat_matrix.append(row_vals)

    v2_row = find_config(rows, V2_REC) or rec

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OpsWarden · RAG 三参数联合调优 v3</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  :root{{--orange:#ff6700;--blue:#1a73e8;--green:#34a853;--red:#e0533d;--bg:#f6f7f9;--card:#fff;--text:#1a1a1f;--dim:#6b7280;--line:#e5e7eb}}
  *{{box-sizing:border-box}} body{{margin:0;font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;background:var(--bg);color:var(--text)}}
  .wrap{{max-width:1100px;margin:0 auto;padding:28px 24px 64px}}
  header{{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:28px}}
  header .kick{{font-size:12px;font-weight:800;letter-spacing:.22em;color:var(--orange)}}
  header h1{{margin:.2em 0;font-size:28px;font-weight:900}}
  .grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}} @media(max-width:820px){{.grid{{grid-template-columns:1fr}}}}
  .card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 20px;box-shadow:0 8px 24px -16px rgba(0,0,0,.12)}}
  .card.full{{grid-column:1/-1}} .card h2{{margin:0 0 4px;font-size:16px;font-weight:800}}
  .card .sub{{font-size:12px;color:var(--dim);margin-bottom:14px}}
  .chart-box{{position:relative;height:280px}} .chart-box.tall{{height:320px}}
  .note{{background:#fff3e9;border:1px solid #ffd9bd;border-radius:10px;padding:12px 14px;font-size:13px;margin-top:14px}}
  table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:12px}} th,td{{border:1px solid var(--line);padding:8px;text-align:center}} th{{background:#f1f2f4}}
  .heat{{overflow:auto}} .heat td{{min-width:52px;font-size:11px}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="kick">RAG JOINT3 · v3</div>
    <h1>ε / L1-K / Top-K 联合调优（τ 固定 {tau}）</h1>
    <p>扩库 400 条 · 评测 680 条 · 网格 {len(rows)} 组</p>
  </header>
  <div class="grid">
    <div class="card full">
      <h2>图 1 · ε vs 锚点数 / Hit_para</h2>
      <div class="sub">固定 L1-K={ak_ref}, Top-K={top_k_ref}, τ={tau}</div>
      <div class="chart-box tall"><canvas id="epsChart"></canvas></div>
    </div>
    <div class="card">
      <h2>图 2 · L1-K vs L1_hard / Hit_para</h2>
      <div class="sub">固定 ε={rec['epsilon']}, Top-K={top_k_ref}</div>
      <div class="chart-box"><canvas id="akChart"></canvas></div>
    </div>
    <div class="card">
      <h2>图 3 · Top-K vs Recall@K / Hit_para</h2>
      <div class="sub">固定 ε={rec['epsilon']}, L1-K={ak_ref}</div>
      <div class="chart-box"><canvas id="tkChart"></canvas></div>
    </div>
    <div class="card full">
      <h2>图 4 · ε × L1-K 热力图（Hit_para %）</h2>
      <div class="sub">Top-K={top_k_ref}, τ={tau}</div>
      <div class="heat"><table><tr><th>L1-K \\ ε</th>{''.join(f'<th>{e}</th>' for e in heat_eps)}</tr>
      {''.join(f"<tr><th>{ak}</th>{''.join(f'<td style=\"background:rgba(255,103,0,{min(0.85,v/100):.2f})\">{v}</td>' for v in heat_matrix[i])}</tr>" for i, ak in enumerate(heat_ak))}
      </table></div>
    </div>
    <div class="card full">
      <h2>附表 · v3 推荐 vs v2 推荐</h2>
      <table>
        <tr><th>参数</th><th>v2 推荐</th><th>v3 联合最优</th></tr>
        <tr><td>ε</td><td>{V2_REC['epsilon']}</td><td>{rec['epsilon']}</td></tr>
        <tr><td>L1-K</td><td>{V2_REC['anchor_k']}</td><td>{int(rec['anchor_k'])}</td></tr>
        <tr><td>τ</td><td>{V2_REC['threshold']}</td><td>{rec['threshold']}</td></tr>
        <tr><td>Top-K</td><td>{V2_REC['top_k']}</td><td>{int(rec['top_k'])}</td></tr>
        <tr><td>Hit_para</td><td>{fmt_pct(float(v2_row['hit1_para']))}</td><td>{fmt_pct(float(rec['hit1_para']))}</td></tr>
        <tr><td>L1_hard</td><td>—</td><td>{fmt_pct(float(rec['l1_recall_hard']))}</td></tr>
        <tr><td>Recall@K_para</td><td>—</td><td>{fmt_pct(float(rec['recall_at_k_para']))}</td></tr>
        <tr><td>n_anchors</td><td>100</td><td>{int(rec['n_anchors'])}</td></tr>
        <tr><td>FPR</td><td>{fmt_pct(float(v2_row['fpr']))}</td><td>{fmt_pct(float(rec['fpr']))}</td></tr>
      </table>
      <div class="note">完整报告：<a href="../docs/rag_hyperparam_report_v3_joint.md">rag_hyperparam_report_v3_joint.md</a></div>
    </div>
  </div>
</div>
<script>
Chart.defaults.font.family = '"PingFang SC","Microsoft YaHei",system-ui,sans-serif';
new Chart(document.getElementById('epsChart'), {{
  type:'line',
  data:{{labels:{json.dumps([str(e) for e in epsilons])},datasets:[
    {{label:'Hit_para (%)',data:{json.dumps(eps_hit)},borderColor:'#1a73e8',yAxisID:'y'}},
    {{label:'n_anchors',data:{json.dumps(eps_anchors)},borderColor:'#ff6700',yAxisID:'y1'}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false,scales:{{
    y:{{position:'left',title:{{display:true,text:'Hit %'}}}},
    y1:{{position:'right',grid:{{drawOnChartArea:false}},title:{{display:true,text:'锚点数'}}}}
  }}}}
}});
new Chart(document.getElementById('akChart'), {{
  type:'line',
  data:{{labels:{json.dumps([str(x) for x in anchor_ks])},datasets:[
    {{label:'L1_recall_hard (%)',data:{json.dumps(ak_hard)},borderColor:'#e0533d'}},
    {{label:'Hit_para (%)',data:{json.dumps(ak_hit)},borderColor:'#1a73e8'}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false}}
}});
new Chart(document.getElementById('tkChart'), {{
  type:'bar',
  data:{{labels:{json.dumps([str(x) for x in top_ks])},datasets:[
    {{label:'Recall@K_para (%)',data:{json.dumps(tk_recall)},backgroundColor:'rgba(52,168,83,.75)'}},
    {{label:'Hit@1_para (%)',data:{json.dumps(tk_hit)},backgroundColor:'rgba(26,115,232,.75)'}}
  ]}},
  options:{{responsive:true,maintainAspectRatio:false}}
}});
</script>
</body>
</html>"""
    p["charts"].parent.mkdir(parents=True, exist_ok=True)
    p["charts"].write_text(html, encoding="utf-8")
    print(f"Charts written to {p['charts']}")


def generate_v3_joint_report(p: dict[str, Path]) -> None:
    rows = load_grid(p["grid"])
    float_cols = (
        "epsilon", "threshold", "hit1_exact", "hit1_para", "hit1_hard", "fpr",
        "l1_recall_para", "l1_recall_hard", "recall_at_k_para", "anchor_compression",
        "mrr_para", "score_margin_median", "neg_top_score_median", "neg_top_score_max",
    )
    int_cols = ("anchor_k", "top_k", "n_anchors", "n_kb_entries", "n_exact", "n_paraphrase",
                "n_hard_confusion", "n_negative")
    for row in rows:
        for k, v in row.items():
            try:
                if k in float_cols:
                    row[k] = float(v)
                elif k in int_cols:
                    row[k] = int(float(v))
            except ValueError:
                pass

    ranked = sorted(rows, key=lambda r: config_sort_key_v3_joint(r, FPR_MAX), reverse=True)
    best = ranked[0]
    v2_rec_row = find_config(rows, V2_REC)
    baseline = find_config(rows, BASELINE)

    practical = next(
        (
            r for r in ranked
            if float(r["fpr"]) <= FPR_MAX + 1e-9
            and int(r["anchor_k"]) >= 8
            and float(r["epsilon"]) <= 0.05
            and int(r["top_k"]) == 3
        ),
        None,
    )
    if practical is None:
        pool = [
            r for r in ranked
            if int(r["anchor_k"]) >= 8
            and float(r["epsilon"]) <= 0.05
            and int(r["top_k"]) == 3
        ]
        if pool:
            practical = min(
                pool,
                key=lambda r: (
                    -float(r["hit1_para"]),
                    int(r["anchor_k"]),
                    -float(r["l1_recall_hard"]),
                ),
            )
    rec = practical if practical else best

    top5 = json.loads(p["top5"].read_text(encoding="utf-8")) if p["top5"].exists() else []
    verify = json.loads(p["verify"].read_text(encoding="utf-8")) if p["verify"].exists() else []
    dataset = json.loads(p["dataset"].read_text(encoding="utf-8")) if p["dataset"].exists() else []
    counts: dict[str, int] = {}
    for d in dataset:
        counts[d.get("split", "exact")] = counts.get(d.get("split", "exact"), 0) + 1

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    n_kb = int(rows[0].get("n_kb_entries", 400)) if rows else 400

    lines = [
        "# RAG 三参数联合调优报告（v3 joint3）",
        "",
        f"> 生成时间：{ts}  ",
        f"> 固定 τ = **{FIXED_TAU_V3}**（v2 结论）  ",
        f"> 评测集：exact {counts.get('exact', 0)} + paraphrase {counts.get('paraphrase', 0)} + "
        f"hard_confusion {counts.get('hard_confusion', 0)} + negative {counts.get('negative', 0)} "
        f"= {len(dataset)} 条  ",
        f"> 扩库 KB：**{n_kb}** 条（100 canonical + variants，eval-only）  ",
        f"> 优化目标：FPR≤5% 下最大化 Hit_para，其次 L1_hard / Recall@K / 锚点压缩",
        "",
        "---",
        "",
        "## 1. 相对 v2 的方法升级",
        "",
        "| 维度 | v2 | v3 joint3 |",
        "|------|----|-----------|",
        "| 调参范围 | ε/L1/τ/Top-K 四维 | **固定 τ=0.65**，联合 ε+L1-K+Top-K |",
        "| KB 规模 | 100 FAQ | **400 条**（含 solution 变体，测锚点合并） |",
        "| 查询类型 | exact/para/neg | + **hard_confusion**（同类干扰） |",
        "| 主指标 | Hit_para, FPR | + **L1_recall_hard**, **Recall@K_para**, **anchor_compression** |",
        "",
        f"**网格组合数**：{len(rows)}（8 ε × 9 L1-K × 3 Top-K）",
        "",
        "---",
        "",
        "## 2. 联合最优超参数",
        "",
        "| 参数 | 默认 | v2 推荐 | **v3 联合推荐** | 统计最优 |",
        "|------|------|---------|-----------------|----------|",
        f"| ε | {BASELINE['epsilon']} | {V2_REC['epsilon']} | **{rec['epsilon']}** | {best['epsilon']} |",
        f"| L1-K | {BASELINE['anchor_k']} | {V2_REC['anchor_k']} | **{int(rec['anchor_k'])}** | {int(best['anchor_k'])} |",
        f"| τ | {BASELINE['threshold']} | {V2_REC['threshold']} | **{rec['threshold']}** | {best['threshold']} |",
        f"| Top-K | {BASELINE['top_k']} | {V2_REC['top_k']} | **{int(rec['top_k'])}** | {int(best['top_k'])} |",
        "",
        "### 2.1 主指标",
        "",
        "| 指标 | v3 推荐 | v2 推荐(同网格) | 统计最优 |",
        "|------|---------|-----------------|----------|",
        f"| Hit@1_exact | {fmt_pct(float(rec['hit1_exact']))} | "
        f"{fmt_pct(float(v2_rec_row['hit1_exact'])) if v2_rec_row else 'N/A'} | "
        f"{fmt_pct(float(best['hit1_exact']))} |",
        f"| Hit@1_para | {fmt_pct(float(rec['hit1_para']))} | "
        f"{fmt_pct(float(v2_rec_row['hit1_para'])) if v2_rec_row else 'N/A'} | "
        f"{fmt_pct(float(best['hit1_para']))} |",
        f"| Hit@1_hard | {fmt_pct(float(rec['hit1_hard']))} | — | {fmt_pct(float(best['hit1_hard']))} |",
        f"| FPR | {fmt_pct(float(rec['fpr']))} | "
        f"{fmt_pct(float(v2_rec_row['fpr'])) if v2_rec_row else 'N/A'} | "
        f"{fmt_pct(float(best['fpr']))} |",
        f"| L1_recall_hard | {fmt_pct(float(rec['l1_recall_hard']))} | — | "
        f"{fmt_pct(float(best['l1_recall_hard']))} |",
        f"| Recall@K_para | {fmt_pct(float(rec['recall_at_k_para']))} | — | "
        f"{fmt_pct(float(best['recall_at_k_para']))} |",
        f"| n_anchors | {int(rec['n_anchors'])} | 100 | {int(best['n_anchors'])} |",
        f"| anchor_compression | {float(rec['anchor_compression']):.2f}× | 1.00× | "
        f"{float(best['anchor_compression']):.2f}× |",
        "",
        "### 2.2 推荐 `.env`",
        "",
        "```env",
        f"ANCHOR_QUANT_EPSILON={rec['epsilon']}",
        f"RAG_ANCHOR_TOP_K={int(rec['anchor_k'])}",
        f"RAG_SCORE_THRESHOLD={rec['threshold']}",
        f"RAG_TOP_K={int(rec['top_k'])}",
        "```",
        "",
        "> **边界说明**：扩库为 eval-only；生产若仍 100 条 FAQ，ε/L1-K 的实际收益可能低于 v3 测得值。",
        "",
        f"> **FPR 说明**：v3 负样本扩至 {counts.get('negative', 0)} 条（含 near-miss），"
        f"在 τ=0.65 下全网格 FPR 下限约 **{min(float(r['fpr']) for r in rows)*100:.0f}%**，"
        "高于 v2 的 32 条负样本估计；联合选优以 Hit_para + L1_hard 为主。",
        "",
        "---",
        "",
        "## 3. Top-10 配置（joint3 选优键）",
        "",
        "| Rank | ε | L1-K | Top-K | Hit_para | L1_hard | Recall@K | FPR | n_anchors |",
        "|------|---|------|-------|----------|---------|----------|-----|-----------|",
    ]

    for i, row in enumerate(ranked[:10], start=1):
        lines.append(
            f"| {i} | {row['epsilon']} | {int(row['anchor_k'])} | {int(row['top_k'])} | "
            f"{fmt_pct(float(row['hit1_para']))} | {fmt_pct(float(row['l1_recall_hard']))} | "
            f"{fmt_pct(float(row['recall_at_k_para']))} | {fmt_pct(float(row['fpr']))} | "
            f"{int(row['n_anchors'])} |"
        )

    if verify:
        lines.extend(["", "---", "", "## 4. 双轨复核（DB exact + 内存扩库）", ""])
        lines.append("| Rank | para mem | para verify | hard mem | hard verify | FPR mem | FPR verify |")
        lines.append("|------|----------|-------------|----------|-------------|---------|------------|")
        for row in verify:
            if "error" in row:
                lines.append(f"| — | ERROR | — | — | — | — | {row['error']} |")
                continue
            lines.append(
                f"| {row.get('rank', '—')} | {fmt_pct(float(row['memory_hit1_para']))} | "
                f"{fmt_pct(float(row['db_hit1_para']))} | {fmt_pct(float(row['memory_hit1_hard']))} | "
                f"{fmt_pct(float(row['db_hit1_hard']))} | {fmt_pct(float(row['memory_fpr']))} | "
                f"{fmt_pct(float(row['db_fpr']))} |"
            )

    lines.extend([
        "",
        "---",
        "",
        "## 5. 可视化",
        "",
        f"交互图表：[`rag-hyperparam-v3-joint-charts.html`](../presentation/rag-hyperparam-v3-joint-charts.html)",
        "",
        "## 6. 复现",
        "",
        "```bash",
        "python scripts/build_eval_dataset_v3.py",
        "python scripts/rag_hyperparam_eval.py --dataset v3 --joint3 --all",
        "python scripts/rag_hyperparam_verify_db.py --dataset v3 --joint3",
        "python scripts/generate_rag_report.py --dataset v3 --joint3",
        "```",
        "",
        f"原始数据：[`grid_results_v3_joint.csv`](../scripts/.eval_cache/grid_results_v3_joint.csv)",
        "",
    ])

    p["report"].parent.mkdir(parents=True, exist_ok=True)
    p["report"].write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {p['report']}")
    generate_v3_charts_html(p, rows, rec)


def config_sort_key_v2(row: dict, fpr_max: float) -> tuple:
    fpr = float(row["fpr"])
    return (
        1 if fpr <= fpr_max + 1e-9 else 0,
        float(row["hit1_para"]),
        float(row["threshold"]),
        -fpr,
        -int(row["anchor_k"]),
        float(row["epsilon"]),
        -abs(int(row["top_k"]) - 3),
    )


def find_baseline_v2(rows: list[dict]) -> dict | None:
    for row in rows:
        if (
            abs(float(row["epsilon"]) - BASELINE["epsilon"]) < 1e-9
            and int(row["anchor_k"]) == BASELINE["anchor_k"]
            and abs(float(row["threshold"]) - BASELINE["threshold"]) < 1e-9
            and int(row["top_k"]) == BASELINE["top_k"]
        ):
            return row
    return None


def tau_tradeoff_table(rows: list[dict], epsilon: float, anchor_k: int, top_k: int = 3) -> str:
    subset = [
        r for r in rows
        if abs(float(r["epsilon"]) - epsilon) < 1e-9
        and int(r["anchor_k"]) == anchor_k
        and int(r["top_k"]) == top_k
    ]
    if not subset:
        return "_无数据_\n"
    subset.sort(key=lambda r: float(r["threshold"]))
    lines = [
        f"### τ 权衡表（ε={epsilon}, L1-K={anchor_k}, Top-K={top_k}）",
        "",
        "| τ | Hit@1 exact | Hit@1 para | FPR | L1 para |",
        "|---|-------------|------------|-----|---------|",
    ]
    for r in subset:
        lines.append(
            f"| {float(r['threshold']):.2f} | {fmt_pct(float(r['hit1_exact']))} | "
            f"{fmt_pct(float(r['hit1_para']))} | {fmt_pct(float(r['fpr']))} | "
            f"{fmt_pct(float(r['l1_recall_para']))} |"
        )
    lines.append("")
    return "\n".join(lines)


def generate_v2_report(p: dict[str, Path]) -> None:
    rows = load_grid(p["grid"])
    for row in rows:
        for k, v in row.items():
            try:
                if k in ("epsilon", "threshold", "hit1_exact", "hit1_para", "fpr", "mrr_para",
                         "score_margin_median", "neg_top_score_median", "neg_top_score_max", "l1_recall_para"):
                    row[k] = float(v)
                else:
                    row[k] = int(float(v))
            except ValueError:
                pass

    ranked = sorted(rows, key=lambda r: config_sort_key_v2(r, FPR_MAX), reverse=True)
    best = ranked[0]
    baseline = find_baseline_v2(rows)

    practical = next(
        (
            r for r in ranked
            if float(r["fpr"]) <= FPR_MAX + 1e-9
            and int(r["anchor_k"]) >= 8
            and float(r["epsilon"]) <= 0.02
            and int(r["top_k"]) == 3
        ),
        None,
    )

    top5 = json.loads(p["top5"].read_text(encoding="utf-8")) if p["top5"].exists() else []
    verify = json.loads(p["verify"].read_text(encoding="utf-8")) if p["verify"].exists() else []
    dataset = json.loads(p["dataset"].read_text(encoding="utf-8")) if p["dataset"].exists() else []
    n_exact = sum(1 for d in dataset if d.get("split") == "exact")
    n_para = sum(1 for d in dataset if d.get("split") == "paraphrase")
    n_neg = sum(1 for d in dataset if d.get("split") == "negative")

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    rec = practical if practical else best

    lines = [
        "# RAG 超参数调节实验报告（v2）",
        "",
        f"> 生成时间：{ts}  ",
        f"> 评测集：exact {n_exact} + paraphrase {n_para} + negative {n_neg} = {len(dataset)} 条  ",
        f"> 优化目标：**准确优先**（FPR ≤ {FPR_MAX:.0%} 约束下最大化 Hit@1_para）",
        "",
        "---",
        "",
        "## 0. v1 实验为何不可靠（回顾）",
        "",
        "v1 使用 FAQ **原题 100 条**，540/540 组配置 Hit@1 均为 **100%**，原因：",
        "",
        "1. query 与 KB question 字面相同（自匹配上界）",
        "2. 无负样本，无法测量误命中",
        "3. τ 网格上限 0.60 低于最小正确分 0.867",
        "4. 100 条 FAQ 量化后仍 100 个独立锚点，ε/L1-K 无区分度",
        "",
        "v2 通过 **口语改写 + 负样本 + 扩展 τ 至 0.85** 修复上述问题。",
        "",
        "---",
        "",
        "## 1. 实验设置",
        "",
        "| 参数 | 候选值 |",
        "|------|--------|",
        "| `ANCHOR_QUANT_EPSILON` | 0.01 – 0.10（6 档） |",
        "| `RAG_ANCHOR_TOP_K` | 1, 2, 3, 4, 8, 12, 16, 24 |",
        "| `RAG_SCORE_THRESHOLD` | 0.35 – 0.85（步长 0.05） |",
        "| `RAG_TOP_K` | 1, 3, 5 |",
        "",
        f"**总组合数**：{len(rows)}",
        "",
        "### 指标",
        "",
        "| 指标 | 说明 |",
        "|------|------|",
        "| Hit@1_exact | 原题子集命中率（上界） |",
        "| Hit@1_para | **改写子集命中率（主指标）** |",
        "| FPR | 负样本 Top-1 分数 ≥ τ 的比例 |",
        "| L1_recall_para | 改写集锚点召回 |",
        "| MRR_para | 改写集 MRR |",
        "",
        "---",
        "",
        "## 2. 最优超参数（v2 内存网格）",
        "",
        "| 参数 | 当前默认 | **推荐（生产保守）** | 统计最优 |",
        "|------|----------|----------------------|----------|",
        f"| ε | {BASELINE['epsilon']} | **{rec['epsilon']}** | {best['epsilon']} |",
        f"| L1-K | {BASELINE['anchor_k']} | **{int(rec['anchor_k'])}** | {int(best['anchor_k'])} |",
        f"| τ | {BASELINE['threshold']} | **{rec['threshold']}** | {best['threshold']} |",
        f"| Top-K | {BASELINE['top_k']} | **{int(rec['top_k'])}** | {int(best['top_k'])} |",
        "",
        "### 2.1 主指标对比",
        "",
        "| 指标 | 推荐配置 | 当前默认 | 统计最优 |",
        "|------|----------|----------|----------|",
        f"| Hit@1_exact | {fmt_pct(float(rec['hit1_exact']))} | "
        f"{fmt_pct(float(baseline['hit1_exact'])) if baseline else 'N/A'} | "
        f"{fmt_pct(float(best['hit1_exact']))} |",
        f"| Hit@1_para | {fmt_pct(float(rec['hit1_para']))} | "
        f"{fmt_pct(float(baseline['hit1_para'])) if baseline else 'N/A'} | "
        f"{fmt_pct(float(best['hit1_para']))} |",
        f"| FPR | {fmt_pct(float(rec['fpr']))} | "
        f"{fmt_pct(float(baseline['fpr'])) if baseline else 'N/A'} | "
        f"{fmt_pct(float(best['fpr']))} |",
        f"| L1_recall_para | {fmt_pct(float(rec['l1_recall_para']))} | "
        f"{fmt_pct(float(baseline['l1_recall_para'])) if baseline else 'N/A'} | "
        f"{fmt_pct(float(best['l1_recall_para']))} |",
        f"| MRR_para | {float(rec['mrr_para']):.4f} | "
        f"{float(baseline['mrr_para']) if baseline else 0:.4f} | "
        f"{float(best['mrr_para']):.4f} |",
        "",
        "### 2.2 推荐 `.env`",
        "",
        "```env",
        f"ANCHOR_QUANT_EPSILON={rec['epsilon']}",
        f"RAG_ANCHOR_TOP_K={int(rec['anchor_k'])}",
        f"RAG_SCORE_THRESHOLD={rec['threshold']}",
        f"RAG_TOP_K={int(rec['top_k'])}",
        "```",
        "",
        "---",
        "",
        "## 3. Top-10 配置（FPR≤5% 优先）",
        "",
        "| Rank | ε | L1-K | τ | Top-K | Hit_para | FPR | Hit_exact | L1_para |",
        "|------|---|------|---|-------|----------|-----|-----------|---------|",
    ]

    for i, row in enumerate(ranked[:10], start=1):
        lines.append(
            f"| {i} | {row['epsilon']} | {int(row['anchor_k'])} | {row['threshold']} | "
            f"{int(row['top_k'])} | {fmt_pct(float(row['hit1_para']))} | "
            f"{fmt_pct(float(row['fpr']))} | {fmt_pct(float(row['hit1_exact']))} | "
            f"{fmt_pct(float(row['l1_recall_para']))} |"
        )

    lines.extend(["", "---", "", "## 4. τ 权衡曲线（推荐 ε/L1-K 切片）", ""])
    lines.append(tau_tradeoff_table(rows, float(rec["epsilon"]), int(rec["anchor_k"])))
    if baseline:
        lines.append(tau_tradeoff_table(rows, float(baseline["epsilon"]), int(baseline["anchor_k"])))

    if verify:
        lines.extend(["---", "", "## 5. PostgreSQL 复核", ""])
        lines.append("| Rank | Hit_para mem | Hit_para DB | FPR mem | FPR DB | Δpara | Δfpr |")
        lines.append("|------|--------------|-------------|---------|--------|-------|------|")
        for row in verify:
            if "error" in row:
                lines.append(f"| — | ERROR | — | — | — | — | {row['error']} |")
                continue
            lines.append(
                f"| {row.get('rank', '—')} | {fmt_pct(float(row['memory_hit1_para']))} | "
                f"{fmt_pct(float(row['db_hit1_para']))} | {fmt_pct(float(row['memory_fpr']))} | "
                f"{fmt_pct(float(row['db_fpr']))} | {row['delta_hit1_para']:+.3f} | {row['delta_fpr']:+.3f} |"
            )
        neg_fp = int(round(float(rec["fpr"]) * n_neg))
        lo, hi = wilson_ci(neg_fp, n_neg)
        lines.extend([
            "",
            f"> FPR 95% Wilson 区间（推荐配置, n={n_neg}）：[{lo:.3f}, {hi:.3f}]（小样本估计）",
        ])

    lines.extend([
        "",
        "---",
        "",
        "## 6. 结论",
        "",
        f"1. v2 在改写集上 Hit@1_para 约 **{fmt_pct(float(rec['hit1_para']))}**，FPR 约 **{fmt_pct(float(rec['fpr']))}**，较 v1 具备区分度",
        f"2. 相对默认 (0.02/8/0.4/3)，推荐将 τ 调整为 **{rec['threshold']}**",
        "3. 负样本仅 32 条，FPR 估计有方差；生产环境建议持续收集真实未命中/误命中日志迭代",
        "",
        "## 附录：复现",
        "",
        "```bash",
        "python scripts/build_eval_dataset_v2.py",
        "python scripts/rag_hyperparam_eval.py --dataset v2 --all",
        "python scripts/rag_hyperparam_verify_db.py --dataset v2",
        "python scripts/generate_rag_report.py --dataset v2",
        "```",
        "",
        f"原始数据：[`grid_results_v2.csv`](../scripts/.eval_cache/grid_results_v2.csv)",
        "",
    ])

    p["report"].parent.mkdir(parents=True, exist_ok=True)
    p["report"].write_text("\n".join(lines), encoding="utf-8")
    print(f"Report written to {p['report']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", choices=["v1", "v2", "v3"], default="v2")
    parser.add_argument("--joint3", action="store_true")
    args = parser.parse_args()
    if args.dataset == "v3" and not args.joint3:
        args.joint3 = True
    p = paths_for(args.dataset)
    if not p["grid"].exists():
        raise FileNotFoundError(f"Run grid first: {p['grid']}")
    if args.dataset == "v3":
        generate_v3_joint_report(p)
    elif args.dataset == "v2":
        generate_v2_report(p)
    else:
        generate_v2_report(p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
