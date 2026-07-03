#!/usr/bin/env python3
"""V2 RAG 范式对比实验 CLI 入口。

Usage:
    # 烟测：5 场景 × 6 范式在 N=400 上（不开 BGE 嵌入，--smoke 自动用前 100 query）
    python scripts/run_paradigm_benchmark_v2.py --scenario all --smoke

    # 完整 benchmark（V2 全量）
    python scripts/run_paradigm_benchmark_v2.py --scenario all --repeats 3 --top-k 3

    # 单场景
    python scripts/run_paradigm_benchmark_v2.py --scenario S1
    python scripts/run_paradigm_benchmark_v2.py --scenario S2 --kb-size 10000
    python scripts/run_paradigm_benchmark_v2.py --scenario S4

    # 不含 GridTrace+（V1 baseline 重现）
    python scripts/run_paradigm_benchmark_v2.py --scenario all --no-enhanced
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS = ROOT / "experiments"
BENCH = EXPERIMENTS / "paradigm_benchmark"
if str(EXPERIMENTS) not in sys.path:
    sys.path.insert(0, str(EXPERIMENTS))
if str(BENCH) not in sys.path:
    sys.path.insert(0, str(BENCH))

from paradigm_benchmark.runner_v2 import run_all_scenarios, run_scenario, save_v2_results  # noqa: E402
from paradigm_benchmark.report_v2 import render_report  # noqa: E402
from paradigm_benchmark.scenarios import ALL_SCENARIOS  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("paradigm_benchmark_v2_cli")


def main() -> None:
    parser = argparse.ArgumentParser(description="V2 RAG 范式对比实验 CLI")
    parser.add_argument(
        "--scenario",
        default="all",
        choices=["all", "S1", "S2", "S3", "S4", "S5"],
        help="要跑的场景（all / S1~S5）",
    )
    parser.add_argument("--repeats", type=int, default=3, help="每个 query 重复次数取中位数")
    parser.add_argument("--top-k", type=int, default=3, help="检索 top_k")
    parser.add_argument("--sla-ms", type=float, default=30.0, help="SLA 阈值（ms）")
    parser.add_argument(
        "--kb-size",
        type=int,
        default=None,
        help="指定 KB 规模（覆盖场景默认；用于 S2 单独跑某个 size）",
    )
    parser.add_argument(
        "--scale-sizes",
        default="1000,5000,10000,50000",
        help="S2 规模化场景的 size 列表（逗号分隔）",
    )
    parser.add_argument(
        "--no-enhanced",
        action="store_true",
        help="不跑 GridTrace+ 增强版（只跑 V1 的 5 范式）",
    )
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="烟测模式（每个场景 query 数 ≤ 30）",
    )
    parser.add_argument(
        "--results-json",
        default="docs/PARADIGM_BENCHMARK_V2_RESULTS.json",
        help="结果 JSON 输出路径",
    )
    parser.add_argument(
        "--output",
        default="docs/PARADIGM_BENCHMARK_V2_REPORT.md",
        help="Markdown 报告输出路径",
    )
    args = parser.parse_args()

    use_enhanced = not args.no_enhanced
    scale_sizes = [int(s) for s in args.scale_sizes.split(",")]

    # 烟测模式：每个场景 query 数 ≤ 30
    smoke_n = 30 if args.smoke else None
    if smoke_n:
        for spec in ALL_SCENARIOS.values():
            existing_nq = spec.extra.get("n_queries") or 200
            spec.extra["n_queries"] = min(existing_nq, smoke_n)
            existing_per_size = spec.extra.get("n_queries_per_size") or 100
            spec.extra["n_queries_per_size"] = min(existing_per_size, smoke_n)
            existing_test = spec.extra.get("n_test_queries") or 100
            spec.extra["n_test_queries"] = min(existing_test, smoke_n)
        logger.info("烟测模式：每个场景 query 数 ≤ %d", smoke_n)

    # 跑指定场景
    if args.scenario == "all":
        results = run_all_scenarios(
            top_k=args.top_k,
            repeats=args.repeats,
            sla_ms=args.sla_ms,
            scale_sizes=scale_sizes,
            use_enhanced=use_enhanced,
        )
    else:
        spec = ALL_SCENARIOS[args.scenario]
        if spec.id == "S2" and args.kb_size is not None:
            # 单个 size
            results = {args.scenario: run_scenario(
                spec,
                target_size=args.kb_size,
                top_k=args.top_k,
                repeats=args.repeats,
                sla_ms=args.sla_ms,
                use_enhanced=use_enhanced,
            )}
        else:
            results = {args.scenario: run_scenario(
                spec,
                target_size=args.kb_size,
                top_k=args.top_k,
                repeats=args.repeats,
                sla_ms=args.sla_ms,
                use_enhanced=use_enhanced,
            )}

    # 保存结果
    save_v2_results(results, Path(args.results_json))
    logger.info("结果已保存: %s", args.results_json)

    # 渲染报告
    render_report(results, args.output)
    logger.info("报告已生成: %s", args.output)


if __name__ == "__main__":
    main()
