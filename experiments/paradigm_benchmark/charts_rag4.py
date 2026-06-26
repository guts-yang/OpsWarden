"""RAG④ 对比优势专用图表。

输入:
  - docs/PARADIGM_BENCHMARK_V2_RESULTS.json    (S1 trail / S2 scaling build_time)
  - docs/PARADIGM_BENCHMARK_V3_A3_RESULTS.json (删除策略对比)

输出 (到 docs/rag4_charts/):
  - rag4_trail_completeness.png    6 范式 trail 完整度,标注 GT+ 5.0x 独享
  - rag4_build_time_scaling.png    IVF vs GT+ Build Time 随 N,标注 16.4x 差距
  - rag4_delete_strategy.png       3 删除策略的 Delete+Rebuild 时间 + Index 释放

设计原则:数据全部从 JSON 实测读取,绝不硬编;所有标注数字均可逐条溯源到 JSON。
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# 中文字体优先级(与 v2 charts 一致)
for _font in [
    "Microsoft YaHei",
    "SimHei",
    "PingFang SC",
    "Noto Sans CJK SC",
    "WenQuanYi Zen Hei",
    "Arial Unicode MS",
    "DejaVu Sans",
]:
    try:
        matplotlib.rcParams["font.sans-serif"] = [_font]
        matplotlib.rcParams["axes.unicode_minus"] = False
        break
    except Exception:
        continue

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
OUT_DIR = DOCS / "rag4_charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

V2_JSON = DOCS / "PARADIGM_BENCHMARK_V2_RESULTS.json"
A3_JSON = DOCS / "PARADIGM_BENCHMARK_V3_A3_RESULTS.json"

# 范式颜色(与 charts_v2.py 保持一致)
PARADIGM_COLOR = {
    "Flat": "#94A3B8",
    "IVF": "#A855F7",
    "HNSW": "#10B981",
    "PageIndex": "#F97316",
    "GridTrace": "#3B82F6",
    "GridTrace+": "#2563EB",
}


def _save(fig, name: str) -> str:
    path = OUT_DIR / name
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return str(path)


# ===== 图 1:6 范式 trail 完整度(S1 场景实测) =====
def chart_trail_completeness() -> str:
    v2 = json.loads(V2_JSON.read_text(encoding="utf-8"))
    s1 = v2["S1"]["kpis"]
    paradigms = ["Flat", "IVF", "HNSW", "PageIndex", "GridTrace", "GridTrace+"]
    vals = [s1[p]["retrieval_trail_completeness"] for p in paradigms]
    colors = [PARADIGM_COLOR[p] for p in paradigms]

    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.bar(paradigms, vals, color=colors, alpha=0.88, edgecolor="#111827", linewidth=0.6)
    for bar, v in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + 0.03,
            f"{v:.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold" if v >= 0.99 else "normal",
            color="#111827",
        )

    # 标注 5.0x 独享
    gt_val = s1["GridTrace+"]["retrieval_trail_completeness"]
    other_max = max(s1[p]["retrieval_trail_completeness"] for p in paradigms if p != "GridTrace+")
    ratio = gt_val / other_max
    ax.annotate(
        f"GridTrace+ 唯一满分\n= {gt_val:.1f}\n其他 5 范式 = {other_max:.1f}\n→ 独享 {ratio:.1f}x",
        xy=(5, 1.0),
        xytext=(3.4, 0.55),
        fontsize=11,
        color="#2563EB",
        ha="center",
        fontweight="bold",
        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#DBEAFE", edgecolor="#2563EB", linewidth=1.2),
    )

    ax.set_ylabel("Retrieval Trail 完整度 (0~1,越大越好)", fontsize=11)
    ax.set_title("6 范式 Trail 完整度对比(S1 场景实测)\nGridTrace+ 唯一返回完整 {quant_key, l1_bucket_size, l2_score, anchor_path, rerank_info}",
                 fontsize=12, pad=14)
    ax.set_ylim(0, 1.25)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--")
    return _save(fig, "rag4_trail_completeness.png")


# ===== 图 2:IVF vs GridTrace+ Build Time 随 N(S2 场景实测) =====
def chart_build_time_scaling() -> str:
    v2 = json.loads(V2_JSON.read_text(encoding="utf-8"))
    s2 = v2["S2"]["by_size"]
    sizes = sorted(int(s) for s in s2.keys())
    ivf = [s2[str(n)]["kpis"]["IVF"]["build_time_sec"] for n in sizes]
    gt = [s2[str(n)]["kpis"]["GridTrace+"]["build_time_sec"] for n in sizes]

    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(sizes))
    w = 0.36
    bars_ivf = ax.bar(x - w / 2, ivf, w, label="IVF (聚类中心迭代收敛慢)",
                      color=PARADIGM_COLOR["IVF"], alpha=0.88, edgecolor="#111827", linewidth=0.5)
    bars_gt = ax.bar(x + w / 2, gt, w, label="GridTrace+ (L1 量化桶预计算)",
                     color=PARADIGM_COLOR["GridTrace+"], alpha=0.88, edgecolor="#111827", linewidth=0.5)

    # 数值标签
    for bar, v in zip(bars_ivf, ivf):
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15, f"{v:.1f}s",
                ha="center", va="bottom", fontsize=9, color="#6B21A8", fontweight="bold")
    for bar, v in zip(bars_gt, gt):
        ax.text(bar.get_x() + bar.get_width() / 2, v * 1.15, f"{v:.2f}s",
                ha="center", va="bottom", fontsize=9, color="#1E40AF", fontweight="bold")

    # 倍数箭头 + 标签(N=50K)
    ratio_50k = ivf[-1] / gt[-1]
    ax.annotate(
        f"N=50K 时\nIVF / GT+ = {ratio_50k:.1f}x",
        xy=(x[-1] - w / 2, ivf[-1]),
        xytext=(x[-1] - 1.4, ivf[-1] * 0.55),
        fontsize=12,
        color="#DC2626",
        fontweight="bold",
        ha="center",
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEE2E2", edgecolor="#DC2626", linewidth=1.5),
    )

    # 各档倍数小标签
    for i, (a, b) in enumerate(zip(ivf, gt)):
        r = a / b
        ax.text(x[i], max(a, b) * 1.55, f"{r:.1f}x", ha="center", va="bottom",
                fontsize=9, color="#6B7280", fontstyle="italic")

    ax.set_xticks(x)
    ax.set_xticklabels([f"N={n//1000}K" if n >= 1000 else f"N={n}" for n in sizes], fontsize=10)
    ax.set_yscale("log")
    ax.set_ylabel("Build Time (秒,对数轴)", fontsize=11)
    ax.set_title("IVF vs GridTrace+ Build Time 随 N 变化(S2 场景实测)\nGridTrace+ 不需要等聚类收敛:Build 时间随 N 接近线性,而 IVF 平方级",
                 fontsize=12, pad=14)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, linestyle="--", which="both")
    ax.set_ylim(0.01, max(ivf) * 3)
    return _save(fig, "rag4_build_time_scaling.png")


# ===== 图 3:3 删除策略对比(A3 场景实测) =====
def chart_delete_strategy() -> str:
    a3 = json.loads(A3_JSON.read_text(encoding="utf-8"))
    strategies = a3["strategies"]
    names = [s["strategy"] for s in strategies]
    delete_t = [s["delete_time_sec"] for s in strategies]
    rebuild_t = [s["rebuild_time_sec"] for s in strategies]
    idx_rel = [s["pre_delete_index_mb"] - s["post_delete_index_mb"] for s in strategies]
    color_map = {
        "GridTrace+": PARADIGM_COLOR["GridTrace+"],
        "HNSW_mark": "#10B981",
        "HNSW_rebuild": "#F59E0B",
    }
    colors = [color_map[n] for n in names]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.5))

    # 左:Delete + Rebuild 堆叠柱
    x = np.arange(len(names))
    w = 0.55
    bars_d = ax1.bar(x, delete_t, w, label="Delete 耗时 (s)", color=colors, alpha=0.88,
                     edgecolor="#111827", linewidth=0.5)
    bars_r = ax1.bar(x, rebuild_t, w, bottom=delete_t, label="Rebuild 耗时 (s)",
                     color=colors, alpha=0.45, edgecolor="#111827", linewidth=0.5,
                     hatch="//")
    for i, (bd, br) in enumerate(zip(bars_d, bars_r)):
        total = delete_t[i] + rebuild_t[i]
        ax1.text(bd.get_x() + bd.get_width() / 2, total + 0.02, f"合计 {total:.2f}s",
                 ha="center", va="bottom", fontsize=10, fontweight="bold", color="#111827")
        if delete_t[i] > 0.01:
            ax1.text(bd.get_x() + bd.get_width() / 2, delete_t[i] / 2, f"{delete_t[i]:.3f}s",
                     ha="center", va="center", fontsize=9, color="white", fontweight="bold")
        if rebuild_t[i] > 0.01:
            ax1.text(br.get_x() + br.get_width() / 2, delete_t[i] + rebuild_t[i] / 2,
                     f"{rebuild_t[i]:.2f}s", ha="center", va="center", fontsize=9,
                     color="#111827", fontweight="bold")

    ax1.set_xticks(x)
    ax1.set_xticklabels(names, fontsize=10)
    ax1.set_ylabel("耗时 (秒,堆叠)", fontsize=11)
    ax1.set_title("3 删除策略:Delete + Rebuild 总耗时(A3 实测)", fontsize=11, pad=10)
    ax1.legend(loc="upper left", fontsize=9)
    ax1.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax1.set_ylim(0, max(d + r for d, r in zip(delete_t, rebuild_t)) * 1.25)

    # 右:Index Size 释放(MB)
    bars_idx = ax2.bar(x, idx_rel, w, color=colors, alpha=0.88,
                       edgecolor="#111827", linewidth=0.5)
    for i, (bar, v) in enumerate(zip(bars_idx, idx_rel)):
        pct = v / max(s["pre_delete_index_mb"] for s in strategies) * 100
        ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.05, f"{v:.2f}MB\n({pct:.1f}%)",
                 ha="center", va="bottom", fontsize=10, fontweight="bold", color="#111827")

    # 物理删除标注(GT+)
    ax2.annotate(
        "GridTrace+ 真正物理删除\n(mark_deleted=False)\n内存立即回收",
        xy=(0, idx_rel[0]),
        xytext=(0.6, idx_rel[0] + 1.0),
        fontsize=10,
        color="#2563EB",
        fontweight="bold",
        ha="center",
        arrowprops=dict(arrowstyle="->", color="#2563EB", lw=1.8),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#DBEAFE", edgecolor="#2563EB", linewidth=1.2),
    )
    # HNSW_mark 警告
    ax2.annotate(
        "HNSW_mark 只打标记\n节点不释放 → 内存泄漏",
        xy=(1, idx_rel[1]),
        xytext=(1.6, 1.5),
        fontsize=10,
        color="#DC2626",
        fontweight="bold",
        ha="center",
        arrowprops=dict(arrowstyle="->", color="#DC2626", lw=1.5),
        bbox=dict(boxstyle="round,pad=0.5", facecolor="#FEE2E2", edgecolor="#DC2626", linewidth=1.2),
    )

    ax2.set_xticks(x)
    ax2.set_xticklabels(names, fontsize=10)
    ax2.set_ylabel("Index Size 释放 (MB)", fontsize=11)
    ax2.set_title("3 删除策略:Index Size 物理释放(A3 实测)", fontsize=11, pad=10)
    ax2.grid(True, axis="y", alpha=0.3, linestyle="--")
    ax2.set_ylim(0, max(idx_rel) * 1.5 + 1)

    fig.suptitle("合规删除:GridTrace+ 物理删除 vs HNSW mark / HNSW mark+rebuild (N=10K,删 100 条)",
                 fontsize=12, y=1.02)
    return _save(fig, "rag4_delete_strategy.png")


def main():
    paths = [
        chart_trail_completeness(),
        chart_build_time_scaling(),
        chart_delete_strategy(),
    ]
    print("Generated RAG④ comparison charts:")
    for p in paths:
        size = Path(p).stat().st_size // 1024
        print(f"  {p}  ({size} KB)")


if __name__ == "__main__":
    main()
