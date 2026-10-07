#!/usr/bin/env python3
"""
Customer Contribution After Cost-to-Serve — single orchestration entrypoint.

Usage:
  python run_pipeline.py              # full pipeline
  python run_pipeline.py --skip-download
  python run_pipeline.py --through finance
  python run_pipeline.py --tests
  python run_pipeline.py --dashboard
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_mod(module: str) -> None:
    print(f"\n{'='*60}\n>> {module}\n{'='*60}")
    env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": str(ROOT)}
    r = subprocess.run(
        [sys.executable, "-m", module],
        cwd=str(ROOT),
        env=env,
    )
    if r.returncode != 0:
        raise SystemExit(f"Step failed: {module} (exit {r.returncode})")


def main():
    parser = argparse.ArgumentParser(description="Customer Contribution After Cost-to-Serve pipeline")
    parser.add_argument("--skip-download", action="store_true", help="Do not attempt data download")
    parser.add_argument(
        "--through",
        choices=["download", "order_line", "finance", "cts", "robustness", "scenarios", "insights", "all"],
        default="all",
        help="Run through this stage (inclusive)",
    )
    parser.add_argument("--tests", action="store_true", help="Run pytest after pipeline")
    parser.add_argument("--dashboard", action="store_true", help="Launch Streamlit after pipeline")
    parser.add_argument("--optional-data", action="store_true", help="Also download optional Olist CSVs")
    args = parser.parse_args()

    stages = [
        ("download", None),
        ("order_line", "src.cleaning.build_order_line"),
        ("finance", "src.finance.product_contribution"),
        ("cts", "src.cost_to_serve.pools_and_allocation"),
        ("robustness", "src.robustness.engine"),
        ("scenarios", "src.scenarios.decision_scenarios"),
        ("insights", None),
    ]
    order = [s[0] for s in stages]
    stop_at = args.through if args.through != "all" else order[-1]
    stop_idx = order.index(stop_at)

    if stop_idx >= 0 and not args.skip_download:
        print(f"\n{'='*60}\n>> ensure Olist data\n{'='*60}")
        sys.path.insert(0, str(ROOT))
        from src.ingestion.download_olist import ensure_olist_data
        ensure_olist_data(include_optional=args.optional_data)
    elif args.skip_download:
        from src.ingestion.download_olist import data_ready, RAW_DIR, verify_row_counts
        if not data_ready():
            raise SystemExit(f"Raw data missing under {RAW_DIR} and --skip-download was set.")
        verify_row_counts(RAW_DIR, strict=True)

    if stop_idx >= 1:
        run_mod("src.cleaning.build_order_line")
    if stop_idx >= 2:
        run_mod("src.finance.product_contribution")
    if stop_idx >= 3:
        run_mod("src.cost_to_serve.pools_and_allocation")
    if stop_idx >= 4:
        run_mod("src.robustness.engine")
    if stop_idx >= 5:
        run_mod("src.scenarios.decision_scenarios")
    if stop_idx >= 6:
        run_mod("src.cost_to_serve.tipping_and_freight")
        run_mod("src.cost_to_serve.honest_economics")
        run_mod("src.cost_to_serve.economic_robustness")
        run_mod("src.cost_to_serve.rank_diagnostics")
        run_mod("src.cost_to_serve.order_economics")
        run_mod("src.cost_to_serve.monte_carlo_sensitivity")
        run_mod("src.scenarios.impact_effort")

    print(f"\n{'='*60}\nPipeline finished through: {stop_at}\n{'='*60}")

    if args.tests:
        print("\n>> pytest")
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q"], cwd=str(ROOT))
        if r.returncode != 0:
            raise SystemExit("Tests failed")

    if args.dashboard:
        print("\n>> streamlit")
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", "app/streamlit_app.py"],
            cwd=str(ROOT),
        )


if __name__ == "__main__":
    main()
