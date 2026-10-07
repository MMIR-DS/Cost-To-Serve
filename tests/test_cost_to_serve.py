"""
Cost-to-Serve allocation & reconciliation tests.
Uses full processed data when available; otherwise falls back to data/sample/.
"""

import pytest
import pandas as pd
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"
OUTPUTS = ROOT / "outputs"


def _load_cts():
    full = PROCESSED / "customer_month_cts.csv"
    sample = SAMPLE / "customer_month_cts_sample.csv"
    if full.exists() and full.stat().st_size > 1000:
        return pd.read_csv(full), "full"
    assert sample.exists(), "No CTS data found. Run pipeline or ensure data/sample exists."
    return pd.read_csv(sample), "sample"


@pytest.fixture(scope="module")
def cm_and_mode():
    return _load_cts()


@pytest.fixture(scope="module")
def cm(cm_and_mode):
    return cm_and_mode[0]


@pytest.fixture(scope="module")
def mode(cm_and_mode):
    return cm_and_mode[1]


@pytest.fixture(scope="module")
def meta():
    path = OUTPUTS / "cts_allocation_meta.json"
    if not path.exists():
        pytest.skip("cts_allocation_meta.json not present (run full pipeline for this check)")
    with open(path) as f:
        return json.load(f)


def test_customer_contribution_identity(cm):
    calc = cm["product_contribution"] - cm["cost_to_serve"]
    assert (abs(cm["customer_contribution"] - calc) < 1e-4).all()


def test_breakeven_and_headroom(cm):
    assert (abs(cm["breakeven_service_cost"] - cm["product_contribution"]) < 1e-4).all()
    assert (
        abs(cm["service_cost_headroom"] - (cm["breakeven_service_cost"] - cm["cost_to_serve"]))
        < 1e-4
    ).all()


def test_no_negative_allocated_costs(cm):
    for col in [
        "cost_order_handling",
        "cost_distribution",
        "cost_warehousing",
        "cost_returns_waste",
    ]:
        if col in cm.columns:
            assert (cm[col] >= -1e-6).all()


def test_service_cost_intensity_range(cm):
    if "service_cost_intensity" not in cm.columns:
        pytest.skip("intensity not in sample")
    valid = cm[cm["net_sales"] > 0]["service_cost_intensity"]
    assert valid.notna().all()
    assert (valid >= 0).all()


def test_positive_and_negative_contributions_exist(cm):
    assert (cm["customer_contribution"] > 0).any()
    assert (cm["customer_contribution"] < 0).any()


def test_avoidable_plus_stranded_equals_pool(cm):
    for pool in ["order_handling", "distribution", "warehousing", "returns_waste"]:
        a, s, c = f"avoidable_{pool}", f"stranded_{pool}", f"cost_{pool}"
        if a in cm.columns and s in cm.columns and c in cm.columns:
            assert (abs(cm[c] - (cm[a] + cm[s])) < 1e-4).all()


def test_pool_reconciliation_if_meta(meta):
    for r in meta.get("reconciliations", []):
        assert abs(r["coverage"] - 1.0) < 1e-6
