"""V2 场景化图表：Pareto / 决策树 / 场景化对比图。"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# 中文字体优先级
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

from .kpi_v2 import KPI_QUALITY, KPI_EFFICIENCY, KPI_COST, KPI_SCENARIO


def _save(fig, path: str) -> str:
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return path


def _color_for_paradigm(name: str) -> str:
    return {
        "Flat": "#94A3B8",
        "IVF": "#A855F7",
        "HNSW": "#10B981",
        "PageIndex": "#F97316",
        "GridTrace": "#3B82F6",
        "GridTrace+": "#2563EB",
    }.get(name, "#6B7280")


# ===== 图：场景化雷达图（每范式 × 5 KPI 维度） =====


def radar_5_paradigms(
    kpis_by_paradigm: dict[str, dict],
    out_dir: str,
    title: str = "六范式五维 KPI 雷达图",
) -> str:
    """雷达图：6 范式 × 5 维度（Hit@1 / p50 / QPS / trail / forget）"""
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    # 5 个维度（归一化到 0~1）
    dims = ["Hit@1", "p50 倒数", "QPS/1000", "可解释性", "1-残余召回"]
    # 计算每个范式每个维度的归一化值
    raw = {}
    for p, kpi in kpis_by_paradigm.items():
        raw[p] = {
            "hit@1": kpi.get("hit@1", 0.0),
            "p50": kpi.get("latency_p50_ms", 1.0),
            "qps": kpi.get("qps", 1.0),
            "trail": kpi.get("retrieval_trail_completeness", 0.0),
            "forget": 1.0 - kpi.get("forget_residual_recall", 0.0),
        }
    # 归一化
    def norm(d):
        max_v = max(d.values()) or 1.0
        return {k: v / max_v for k, v in d.items()}

    normalized = {p: norm(d) for p, d in raw.items()}
    angles = np.linspace(0, 2 * np.pi, len(dims), endpoint=False).tolist()
    angles += angles[:1]
    for p, vals in normalized.items():
        v = [vals["hit@1"], 1.0 - vals["p50"] / max(1e-3, max(d["p50"] for d in raw.values())),
             vals["qps"], vals["trail"], vals["forget"]]
        v += v[:1]
        ax.plot(angles, v, label=p, color=_color_for_paradigm(p), linewidth=2)
        ax.fill(angles, v, alpha=0.1, color=_color_for_paradigm(p))
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dims)
    ax.set_title(title, fontsize=13, pad=20)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    return _save(fig, str(Path(out_dir) / "v2_radar.png"))


# ===== 图：SLA 违约率对比柱状图 =====


def sla_violation_bar(
    kpis_by_paradigm: dict[str, dict],
    out_dir: str,
    title: str = "30ms SLA 违约率（越小越好）",
) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    names = list(kpis_by_paradigm.keys())
    vals = [kpis_by_paradigm[n].get("sla_30ms_violation_rate", 0.0) * 100 for n in names]
    colors = [_color_for_paradigm(n) for n in names]
    bars = ax.bar(names, vals, color=colors, alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v:.1f}%", ha="center")
    ax.set_ylabel("违约率 (%)")
    ax.set_title(title, fontsize=13)
    ax.set_ylim(0, max(vals) * 1.2 + 5)
    return _save(fig, str(Path(out_dir) / "v2_sla_violation.png"))


# ===== 图：合规删除残余召回对比 =====


def forget_residual_bar(
    kpis_by_paradigm: dict[str, dict],
    out_dir: str,
    title: str = "合规删除残余召回率（越小越好）",
) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    names = list(kpis_by_paradigm.keys())
    vals = [kpis_by_paradigm[n].get("forget_residual_recall", 0.0) * 100 for n in names]
    colors = [_color_for_paradigm(n) for n in names]
    bars = ax.bar(names, vals, color=colors, alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.2, f"{v:.1f}%", ha="center")
    ax.set_ylabel("残余召回率 (%)")
    ax.set_title(title, fontsize=13)
    ax.set_ylim(0, max(vals) * 1.2 + 2)
    return _save(fig, str(Path(out_dir) / "v2_forget_residual.png"))


# ===== 图：可解释性完整度对比 =====


def trail_completeness_bar(
    kpis_by_paradigm: dict[str, dict],
    out_dir: str,
    title: str = "Retrieval Trail 完整度（0~1，越大越好）",
) -> str:
    fig, ax = plt.subplots(figsize=(10, 5))
    names = list(kpis_by_paradigm.keys())
    vals = [kpis_by_paradigm[n].get("retrieval_trail_completeness", 0.0) for n in names]
    colors = [_color_for_paradigm(n) for n in names]
    bars = ax.bar(names, vals, color=colors, alpha=0.85)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.01, f"{v:.2f}", ha="center")
    ax.set_ylabel("Trail 完整度")
    ax.set_ylim(0, 1.1)
    ax.set_title(title, fontsize=13)
    return _save(fig, str(Path(out_dir) / "v2_trail_completeness.png"))


# ===== 图：规模化场景下的 p50 折线图 =====


def scaling_p50_curves(
    by_paradigm_size: dict[str, dict[int, float]],
    out_dir: str,
    title: str = "六范式在 N∈{400,1K,5K,10K,50K} 下的 p50 时延（ms，对数轴）",
) -> str:
    """by_paradigm_size: {paradigm: {size: p50_ms}}"""
    fig, ax = plt.subplots(figsize=(10, 6))
    for p, size_to_p50 in by_paradigm_size.items():
        xs = sorted(size_to_p50.keys())
        ys = [size_to_p50[x] for x in xs]
        ax.plot(xs, ys, "-o", label=p, color=_color_for_paradigm(p), linewidth=2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("知识库规模 N")
    ax.set_ylabel("p50 时延 (ms)")
    ax.set_title(title, fontsize=13)
    ax.legend()
    ax.grid(True, alpha=0.3)
    return _save(fig, str(Path(out_dir) / "v2_scaling_p50.png"))


# ===== 图：决策树（用 matplotlib 绘制树状图） =====


def decision_tree_diagram(
    out_dir: str,
    s1_winner: str = "HNSW",
    s2_winner: str = "GridTrace+",
    s3_winner: str = "GridTrace+",
    s4_winner: str = "GridTrace+",
    s5_winner: str = "GridTrace+",
) -> str:
    """渲染"运维 KB 该选哪个范式"决策树。"""
    fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def _box(x, y, w, h, text, color="#E5E7EB", text_color="black"):
        from matplotlib.patches import FancyBboxPatch
        box = FancyBboxPatch(
            (x - w / 2, y - h / 2), w, h,
            boxstyle="round,pad=0.05",
            facecolor=color, edgecolor="#374151", linewidth=1.2,
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=10, color=text_color, wrap=True)

    def _arrow(x1, y1, x2, y2, label=""):
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="->", lw=1.5, color="#374151"))
        if label:
            ax.text((x1 + x2) / 2 + 0.2, (y1 + y2) / 2, label, fontsize=9, color="#6B7280")

    # 根节点
    _box(6, 9.3, 5, 0.7, "你的运维 KB 场景特征？", color="#1F2937", text_color="white")

    # 5 个分支
    branches = [
        (1.5, 7.8, "S1 标准\n小 N + 强 paraphrase", s1_winner, "#10B981"),
        (4, 7.8, "S2 规模化\nN≥1K", s2_winner, "#2563EB"),
        (6.5, 7.8, "S3 热冷\nN=10K 热冷不均", s3_winner, "#2563EB"),
        (9, 7.8, "S4 合规删除\nGDPR / 审计", s4_winner, "#2563EB"),
        (11, 7.8, "S5 可解释性\n需要 retrieval_trail", s5_winner, "#2563EB"),
    ]
    for x, y, label, winner, color in branches:
        _box(x, y, 1.8, 0.9, label, color="#F3F4F6")
        _arrow(6, 9.0, x, y + 0.45)
        # 推荐
        rec = f"推荐\n{winner}"
        rec_color = color if "GridTrace" in winner else ("#10B981" if winner == "HNSW" else "#6B7280")
        _box(x, 5.5, 1.8, 0.9, rec, color=rec_color, text_color="white")
        _arrow(x, y - 0.45, x, 5.5 + 0.45)

    # 兜底层
    _box(6, 3.5, 8, 0.7, "兜底方案：Flat（中小规模，召回最完整）", color="#94A3B8", text_color="white")
    for x, _, _, _, _ in branches:
        _arrow(x, 5.05, 6, 3.85)

    # 不推荐
    _box(6, 1.5, 8, 0.7, "不推荐：PageIndex（无向量；运维 KB 不适合纯 BM25 路由）", color="#FCA5A5", text_color="white")
    ax.set_title("运维 KB 该选哪个 RAG 检索范式？决策树", fontsize=14, pad=20)
    return _save(fig, str(Path(out_dir) / "v2_decision_tree.png"))


# ===== 图：场景化 KPI 热力图（6 范式 × 13 KPI） =====


def kpi_heatmap(
    kpis_by_paradigm: dict[str, dict],
    out_dir: str,
    title: str = "六范式 × 13 KPI 热力图（颜色深 = 越优）",
) -> str:
    from matplotlib.colors import LinearSegmentedColormap

    paradigms = list(kpis_by_paradigm.keys())
    kpi_keys = [
        ("hit@1", "Hit@1 ↑"),
        ("hit@3", "Hit@3 ↑"),
        ("mrr", "MRR ↑"),
        ("ndcg@10", "nDCG@10 ↑"),
        ("latency_p50_ms", "p50 (ms) ↓"),
        ("latency_p95_ms", "p95 (ms) ↓"),
        ("qps", "QPS ↑"),
        ("build_time_sec", "Build(s) ↓"),
        ("index_size_mb", "Index(MB) ↓"),
        ("sla_30ms_violation_rate", "SLA 违约 ↓"),
        ("forget_residual_recall", "残余召回 ↓"),
        ("retrieval_trail_completeness", "Trail ↑"),
    ]
    n_rows = len(kpi_keys)
    n_cols = len(paradigms)
    # 归一化到 0~1（根据 ↑↓ 方向）
    arr = np.zeros((n_rows, n_cols))
    for j, p in enumerate(paradigms):
        kpi = kpis_by_paradigm[p]
        for i, (k, label) in enumerate(kpi_keys):
            v = kpi.get(k, 0.0)
            # 收集该指标所有范式值
            all_vals = [kpis_by_paradigm[pp].get(k, 0.0) for pp in paradigms]
            mn, mx = min(all_vals), max(all_vals)
            if mx == mn:
                arr[i, j] = 0.5
            elif "↓" in label:
                # 越小越好
                arr[i, j] = 1.0 - (v - mn) / (mx - mn)
            else:
                # 越大越好
                arr[i, j] = (v - mn) / (mx - mn)

    fig, ax = plt.subplots(figsize=(11, 7))
    cmap = LinearSegmentedColormap.from_list("opswarden", ["#FEE2E2", "#FEF3C7", "#D1FAE5"])
    im = ax.imshow(arr, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(paradigms, rotation=20, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels([k[1] for k in kpi_keys])
    # 写入数值
    for i in range(n_rows):
        for j in range(n_cols):
            v = kpis_by_paradigm[paradigms[j]].get(kpi_keys[i][0], 0.0)
            txt = f"{v:.3f}" if abs(v) < 10 else f"{v:.1f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8, color="#111827")
    ax.set_title(title, fontsize=13)
    return _save(fig, str(Path(out_dir) / "v2_kpi_heatmap.png"))
