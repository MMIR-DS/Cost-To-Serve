"""Independent recompute cross-checks from order lines vs rates module."""
import pytest
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"
OUTPUTS = ROOT / "outputs"

from src.cost_to_serve.config import POOL_COSTS


def _load_ol():
    full = PROCESSED / "order_line_finance.csv"
    sample = SAMPLE / "order_line_finance_sample.csv"
    path = full if full.exists() and full.stat().st_size > 1000 else sample
    if not path.exists():
        pytest.skip("no order line finance data")
    return pd.read_csv(path, low_memory=False)


def test_hand_recompute_passthrough_negatives():
    ol = _load_ol()
    if "is_canceled" not in ol.columns:
        pytest.skip("missing is_canceled")
    active = ol[~ol["is_canceled"]].copy()
    if len(active) < 50:
        pytest.skip("sample too small")
    orders = active.groupby("order_id", as_index=False).agg(
        n_lines=("order_item_id", "count"),
        net_sales=("net_sales", "sum"),
        product_contribution=("product_contribution", "sum"),
        weight_g=("product_weight_g", "sum"),
    )
    rate_oh = POOL_COSTS["order_handling"] / max(orders["n_lines"].sum(), 1)
    rate_wh = POOL_COSTS["warehousing"] / max(orders["weight_g"].fillna(0).clip(lower=0).sum(), 1e-9)
    contrib = (
        orders["product_contribution"]
        - orders["n_lines"] * rate_oh
        - orders["weight_g"].fillna(0).clip(lower=0) * rate_wh
    )
    n_hand = int((contrib < 0).sum())

    from src.cost_to_serve.rates import compute_order_table
    n_mod = int((compute_order_table(ol)["contrib_passthrough"] < 0).sum())
    assert n_hand == n_mod
    assert 50 <= n_hand <= 200 or len(active) < 1000  # sample mode may differ


def test_rank_diagnostics_if_present():
    path = OUTPUTS / "rank_diagnostics.json"
    if not path.exists():
        pytest.skip("run rank_diagnostics first")
    import json
    s = json.load(open(path))
    w = s["what_allocation_changes"]
    assert w["spearman_contrib_vs_net_sales"] > 0.9
    assert "sign_flips_vs_product_contribution_only" in w


def test_cm_and_order_pass_through_negatives_close():
    import json
    path = OUTPUTS / "economic_robust_classes.json"
    freight = OUTPUTS / "freight_and_tipping_summary.json"
    if not path.exists() or not freight.exists():
        pytest.skip("need pipeline outputs")
    d = json.load(open(path))
    f = json.load(open(freight))
    cm_n = d["baseline_negative_pass_through"]
    order_n = next(c["negative_orders"] for c in f["freight_cases"] if c["case"] == "pass_through")
    assert abs(cm_n - order_n) <= 20
    assert d.get("robust_negative_mixed_with_cancels", 0) <= d["robust_negative"]
