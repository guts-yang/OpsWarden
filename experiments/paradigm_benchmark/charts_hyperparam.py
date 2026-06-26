# -*- coding: utf-8 -*-
"""
RAG 超参数调优图表生成 (V2 1584 组合 + V3 joint3 216 组合)
读 grid_results_v2.csv / grid_results_v3_joint.csv,生成 4 张关键调参图。

输出到 d:/Repositories/OpsWarden/docs/hyperparam_charts/

运行:
  cd d:/Repositories/OpsWarden
  python -m experiments.paradigm_benchmark.charts_hyperparam
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

# 全局风格 — 中文字体优先级(必须把中文字体放第一,否则 DejaVu Sans 抢走)
for _font in ['Microsoft YaHei', 'SimHei', 'PingFang SC',
              'Noto Sans CJK SC', 'WenQuanYi Zen Hei',
              'Arial Unicode MS', 'DejaVu Sans']:
    try:
        plt.rcParams['font.sans-serif'] = [_font]
        plt.rcParams['axes.unicode_minus'] = False
        break
    except Exception:
        continue
plt.rcParams['figure.dpi'] = 110
plt.rcParams['savefig.dpi'] = 150
plt.rcParams['savefig.bbox'] = 'tight'

V2_CSV = r"d:/Repositories/OpsWarden/scripts/.eval_cache/grid_results_v2.csv"
V3_CSV = r"d:/Repositories/OpsWarden/scripts/.eval_cache/grid_results_v3_joint.csv"
OUT_DIR = r"d:/Repositories/OpsWarden/docs/hyperparam_charts"

# 配色
COLORS = {
    'hit_para': '#2563EB',   # 蓝
    'hit_exact': '#10B981',  # 绿
    'hit_hard': '#F59E0B',   # 橙
    'fpr': '#EF4444',        # 红
    'l1_hard': '#8B5CF6',    # 紫
    'rec': '#0EA5E9',        # 天蓝
    'rec_line': '#DC2626',   # 红线(阈值/推荐点)
    'rec_band': '#FEE2E2',   # 红带
    'grid': '#E5E7EB',
    'text': '#1F2937',
    'annot_bg': '#FEF3C7',   # 黄底
}


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def fig1_tau_tradeoff():
    """图1: V2 τ 权衡曲线 (固定 ε=0.02, L1-K=8, Top-K=3)
    双 y 轴: Hit@1_para / Hit@1_exact / FPR
    关键洞察: τ ∈ [0.40, 0.65] 把 FPR 从 81.2% 砸到 3.1%,但 Hit_para 仅掉 1.5pp
    """
    df = pd.read_csv(V2_CSV)
    # 推荐切片: ε=0.02, anchor_k=8, top_k=3
    sub = df[(df['epsilon'] == 0.02) & (df['anchor_k'] == 8) & (df['top_k'] == 3)].copy()
    sub = sub.sort_values('threshold')

    fig, ax_left = plt.subplots(figsize=(10, 5.6))
    ax_right = ax_left.twinx()

    # 左轴: Hit
    ax_left.plot(sub['threshold'], sub['hit1_para'] * 100,
                 'o-', color=COLORS['hit_para'], linewidth=2.6, markersize=8,
                 label='Hit@1 (paraphrase)')
    ax_left.plot(sub['threshold'], sub['hit1_exact'] * 100,
                 's-', color=COLORS['hit_exact'], linewidth=2.0, markersize=7,
                 label='Hit@1 (exact)')

    # 右轴: FPR
    ax_right.plot(sub['threshold'], sub['fpr'] * 100,
                  '^--', color=COLORS['fpr'], linewidth=2.0, markersize=7,
                  label='FPR (negative)')

    # 推荐点 τ=0.65
    rec = sub[sub['threshold'] == 0.65].iloc[0]
    ax_left.axvline(0.65, color=COLORS['rec_line'], linestyle=':', linewidth=1.4, alpha=0.8)
    ax_left.annotate(
        f"τ*=0.65\nFPR {rec['fpr']*100:.1f}%\nHit_para {rec['hit1_para']*100:.1f}%",
        xy=(0.65, rec['hit1_para'] * 100),
        xytext=(0.50, 70),
        fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['annot_bg'], edgecolor='#D97706', linewidth=1.5),
        arrowprops=dict(arrowstyle='->', color='#D97706', lw=1.5),
    )

    # 反差点 τ=0.40 (默认旧值, FPR 81.2%)
    old = sub[sub['threshold'] == 0.40].iloc[0]
    ax_left.annotate(
        f"旧默认 τ=0.40\nFPR {old['fpr']*100:.1f}%\nHit_para {old['hit1_para']*100:.1f}%",
        xy=(0.40, old['hit1_para'] * 100),
        xytext=(0.40, 88),
        fontsize=9.5, color='#7F1D1D',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#FECACA', edgecolor='#DC2626', linewidth=1.2),
    )

    ax_left.set_xlabel('τ (score threshold)', fontsize=12, fontweight='bold')
    ax_left.set_ylabel('Hit@1 (%) — paraphrase / exact', fontsize=11, color='#1E40AF')
    ax_right.set_ylabel('FPR (%) — false positive rate', fontsize=11, color='#B91C1C')
    ax_left.tick_params(axis='y', labelcolor='#1E40AF')
    ax_right.tick_params(axis='y', labelcolor='#B91C1C')
    ax_left.set_ylim(50, 105)
    ax_right.set_ylim(0, 110)
    ax_left.set_xticks(sub['threshold'])
    ax_left.set_xticklabels([f'{t:.2f}' for t in sub['threshold']], rotation=0)
    ax_left.grid(True, alpha=0.3, color=COLORS['grid'])
    ax_left.set_title('Fig.1  τ Trade-off Curve (V2, ε=0.02, L1-K=8, Top-K=3)\n'
                      'Raise τ from 0.40 → 0.65: FPR 81.2% → 3.1% (−78.1pp), Hit_para only −1.5pp',
                      fontsize=12, fontweight='bold', pad=12)

    # 合并图例
    h1, l1 = ax_left.get_legend_handles_labels()
    h2, l2 = ax_right.get_legend_handles_labels()
    ax_left.legend(h1 + h2, l1 + l2, loc='center right', fontsize=9.5, framealpha=0.95)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'hp1_tau_tradeoff.png')
    plt.savefig(out)
    plt.close()
    print(f"[OK] {out}")
    return out


def fig2_v2_grid_heatmap():
    """图2: V2 FPR 热力图 (τ × L1-K) — 展示"安全带"分布
    关键洞察: τ ≥ 0.65 的整行 = 全绿(FPR ≤ 3.1%);τ=0.40 行 = 严重误命中(FPR ≥ 81%)
    纵轴是 L1-K (top_k=3 固定)
    """
    df = pd.read_csv(V2_CSV)
    sub = df[df['top_k'] == 3].copy()
    # pivot: 行=τ, 列=L1-K, 值=FPR
    tau_vals = sorted(sub['threshold'].unique())
    l1_vals = sorted(sub['anchor_k'].unique())
    # 6 个有数据的 ε 都用 (取平均 = 都一样)
    pivot_fpr = sub.groupby(['threshold', 'anchor_k'])['fpr'].mean().unstack()
    pivot_hit = sub.groupby(['threshold', 'anchor_k'])['hit1_para'].mean().unstack()

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.0))

    # 左: FPR
    im1 = axes[0].imshow(pivot_fpr.values * 100, aspect='auto', cmap='RdYlGn_r',
                         vmin=0, vmax=100)
    axes[0].set_xticks(range(len(l1_vals)))
    axes[0].set_xticklabels(l1_vals)
    axes[0].set_yticks(range(len(tau_vals)))
    axes[0].set_yticklabels([f'{t:.2f}' for t in tau_vals])
    axes[0].set_xlabel('L1-K (anchor_k)', fontsize=11, fontweight='bold')
    axes[0].set_ylabel('τ (score threshold)', fontsize=11, fontweight='bold')
    axes[0].set_title('FPR (%) — false positive rate', fontsize=11, fontweight='bold')
    for i in range(len(tau_vals)):
        for j in range(len(l1_vals)):
            v = pivot_fpr.values[i, j]
            color = 'white' if v * 100 > 50 else 'black'
            axes[0].text(j, i, f'{v*100:.1f}', ha='center', va='center', color=color, fontsize=8)
    # 安全带描框 (τ ≥ 0.65)
    safe_row_start = list(tau_vals).index(0.65)
    axes[0].axhline(safe_row_start - 0.5, color='#059669', linewidth=2.5, alpha=0.9)
    plt.colorbar(im1, ax=axes[0], label='FPR (%)')

    # 右: Hit@1_para
    im2 = axes[1].imshow(pivot_hit.values * 100, aspect='auto', cmap='RdYlGn', vmin=60, vmax=100)
    axes[1].set_xticks(range(len(l1_vals)))
    axes[1].set_xticklabels(l1_vals)
    axes[1].set_yticks(range(len(tau_vals)))
    axes[1].set_yticklabels([f'{t:.2f}' for t in tau_vals])
    axes[1].set_xlabel('L1-K (anchor_k)', fontsize=11, fontweight='bold')
    axes[1].set_ylabel('τ (score threshold)', fontsize=11, fontweight='bold')
    axes[1].set_title('Hit@1 paraphrase (%)', fontsize=11, fontweight='bold')
    for i in range(len(tau_vals)):
        for j in range(len(l1_vals)):
            v = pivot_hit.values[i, j]
            color = 'white' if v * 100 < 75 else 'black'
            axes[1].text(j, i, f'{v*100:.1f}', ha='center', va='center', color=color, fontsize=8)
    plt.colorbar(im2, ax=axes[1], label='Hit@1 (%)')

    # 危险带描框 (τ ≤ 0.45)
    danger_row_end = list(tau_vals).index(0.45)
    axes[1].axhline(danger_row_end + 0.5, color='#DC2626', linewidth=2.5, alpha=0.9)

    fig.suptitle('Fig.2  V2 τ × L1-K Heatmap (Top-K=3, ε avg over 6 values)\n'
                 'Green band (τ ≥ 0.65): FPR ≤ 3.1% & Hit_para ≥ 98.5% — 全行安全\n'
                 'Red zone (τ ≤ 0.45): Hit_para = 100% but FPR ≥ 34% — 严重误命中',
                 fontsize=12, fontweight='bold', y=1.03)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'hp2_v2_grid_heatmap.png')
    plt.savefig(out)
    plt.close()
    print(f"[OK] {out}")
    return out


def fig3_v3_l1k_sensitivity():
    """图3: V3 joint3 L1-K 敏感性 (固定 τ=0.65, ε=0.02, Top-K=3)
    4 条线: Hit_para / Hit_hard / L1_hard / FPR
    关键洞察: L1-K=8 已经把 L1_hard 拉到 0.95,L1-K=12 进一步到 0.975 — 边际收益递减
    """
    df = pd.read_csv(V3_CSV)
    sub = df[(df['epsilon'] == 0.02) & (df['top_k'] == 3)].copy()
    sub = sub.sort_values('anchor_k')

    fig, ax = plt.subplots(figsize=(10, 5.6))

    metrics = [
        ('hit1_para', 'Hit@1 (paraphrase)', COLORS['hit_para'], 'o-'),
        ('hit1_hard', 'Hit@1 (hard_confusion)', COLORS['hit_hard'], 's-'),
        ('l1_recall_hard', 'L1 recall (hard)', COLORS['l1_hard'], '^-'),
        ('fpr', 'FPR (negative)', COLORS['fpr'], 'v--'),
    ]
    for col, label, color, marker in metrics:
        ax.plot(sub['anchor_k'], sub[col] * 100, marker, color=color, linewidth=2.4,
                markersize=8, label=label)

    # 推荐点 L1-K=8
    rec = sub[sub['anchor_k'] == 8].iloc[0]
    ax.axvline(8, color=COLORS['rec_line'], linestyle=':', linewidth=1.4, alpha=0.8)
    ax.annotate(
        f"推荐 L1-K=8\nHit_hard {rec['hit1_hard']*100:.1f}%\nL1_hard {rec['l1_recall_hard']*100:.1f}%\nFPR {rec['fpr']*100:.1f}%",
        xy=(8, rec['hit1_hard'] * 100),
        xytext=(10, 35),
        fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['annot_bg'], edgecolor='#D97706', linewidth=1.5),
        arrowprops=dict(arrowstyle='->', color='#D97706', lw=1.5),
    )
    # 边际收益注: L1-K=12 时 L1_hard=0.975
    if 12 in sub['anchor_k'].values:
        sat = sub[sub['anchor_k'] == 12].iloc[0]
        ax.annotate(
            f"L1-K=12 边际收益\nL1_hard {sat['l1_recall_hard']*100:.1f}%\n(只 +2.5pp)",
            xy=(12, sat['l1_recall_hard'] * 100),
            xytext=(15, 90),
            fontsize=9, color='#5B21B6',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#EDE9FE', edgecolor='#7C3AED', linewidth=1.2),
            arrowprops=dict(arrowstyle='->', color='#7C3AED', lw=1.2),
        )

    ax.set_xlabel('L1-K (anchor_k)  —  log scale', fontsize=12, fontweight='bold')
    ax.set_ylabel('Metric value (%)', fontsize=11)
    ax.set_xscale('log')
    ax.set_xticks(sub['anchor_k'])
    ax.set_xticklabels([str(k) for k in sub['anchor_k']])
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3, color=COLORS['grid'])
    ax.set_title('Fig.3  L1-K Sensitivity (V3 joint3, ε=0.02, τ=0.65, Top-K=3)\n'
                 'L1-K=8 is the "knee": L1_hard 0.95 → 0.975 needs L1-K=12 (diminishing return)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.legend(loc='lower right', fontsize=9.5, ncol=2, framealpha=0.95)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'hp3_v3_l1k_sensitivity.png')
    plt.savefig(out)
    plt.close()
    print(f"[OK] {out}")
    return out


def fig4_eps_sensitivity():
    """图4: V3 joint3 ε 敏感性 (固定 L1-K=8, Top-K=3, τ=0.65)
    关键洞察: ε ∈ [0.01, 0.10] 整段都是「平台」,Hit_para 稳定 99.5%
    选 ε=0.02 兼顾「精度高 + 锚点合并好」双目标
    """
    df = pd.read_csv(V3_CSV)
    sub = df[(df['anchor_k'] == 8) & (df['top_k'] == 3)].copy()
    sub = sub.sort_values('epsilon')

    fig, ax = plt.subplots(figsize=(10, 5.4))
    ax.plot(sub['epsilon'], sub['hit1_para'] * 100, 'o-', color=COLORS['hit_para'],
            linewidth=2.6, markersize=8, label='Hit@1 (paraphrase)')
    ax.plot(sub['epsilon'], sub['hit1_hard'] * 100, 's-', color=COLORS['hit_hard'],
            linewidth=2.4, markersize=7, label='Hit@1 (hard_confusion)')
    ax.plot(sub['epsilon'], sub['fpr'] * 100, '^--', color=COLORS['fpr'],
            linewidth=2.0, markersize=7, label='FPR (negative)')

    # 推荐点
    rec = sub[sub['epsilon'] == 0.02].iloc[0]
    ax.axvline(0.02, color=COLORS['rec_line'], linestyle=':', linewidth=1.4, alpha=0.8)
    ax.annotate(
        f"推荐 ε=0.02\nHit_para {rec['hit1_para']*100:.1f}%\nHit_hard {rec['hit1_hard']*100:.1f}%\nFPR {rec['fpr']*100:.1f}%",
        xy=(0.02, rec['hit1_para'] * 100),
        xytext=(0.04, 75),
        fontsize=10, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.5', facecolor=COLORS['annot_bg'], edgecolor='#D97706', linewidth=1.5),
        arrowprops=dict(arrowstyle='->', color='#D97706', lw=1.5),
    )

    ax.set_xlabel('ε (quantization step)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Metric value (%)', fontsize=11)
    ax.set_xticks(sub['epsilon'])
    ax.set_xticklabels([f'{e:.2f}' for e in sub['epsilon']], rotation=0)
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3, color=COLORS['grid'])
    ax.set_title('Fig.4  ε Sensitivity (V3 joint3, L1-K=8, τ=0.65, Top-K=3)\n'
                 'ε ∈ [0.01, 0.10] is a "plateau" — Hit_para ≥ 99.5%, FPR ≤ 13% all hold',
                 fontsize=12, fontweight='bold', pad=12)
    ax.legend(loc='lower left', fontsize=10, framealpha=0.95)

    plt.tight_layout()
    out = os.path.join(OUT_DIR, 'hp4_eps_sensitivity.png')
    plt.savefig(out)
    plt.close()
    print(f"[OK] {out}")
    return out


def main():
    ensure_out_dir()
    print("=" * 60)
    print("RAG 超参调优图表生成  (V2 1584 + V3 216 = 1800 组)")
    print("=" * 60)
    fig1_tau_tradeoff()
    fig2_v2_grid_heatmap()
    fig3_v3_l1k_sensitivity()
    fig4_eps_sensitivity()
    print("=" * 60)
    print("All 4 charts generated.")
    for f in sorted(os.listdir(OUT_DIR)):
        size = os.path.getsize(os.path.join(OUT_DIR, f))
        print(f"  {f:35s}  {size/1024:6.1f} KB")
    print("=" * 60)


if __name__ == '__main__':
    main()
