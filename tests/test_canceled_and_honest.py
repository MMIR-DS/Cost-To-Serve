"""Canceled-driver fix and non-fulfillment separation."""
import pytest
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
SAMPLE = ROOT / "data" / "sample"
OUTPUTS = ROOT / "outputs"


@pytest.fixture(scope="module")
def cm():
    full = PROCESSED / "customer_month_cts.csv"
    sample = SAMPLE / "customer_month_cts_sample.csv"
    path = full if full.exists() and full.stat().st_size > 1000 else sample
    return pd.read_csv(path)


def test_non_fulfillment_has_zero_logistics_drivers(cm):
    """Pure non-fulfillment CM must not carry OH/Dist/WH cost."""
    if "n_order_lines" not in cm.columns:
        pytest.skip("missing columns")
    nf = cm[(cm["n_order_lines"] == 0) & (cm.get("n_canceled_lines", 0) > 0)]
    if len(nf) == 0:
        pytest.skip("no pure non-fulfillment in this data slice")
    for col in ["cost_order_handling", "cost_distribution", "cost_warehousing"]:
        if col in nf.columns:
            assert (nf[col].fillna(0) == 0).all(), f"{col} should be 0 for non-fulfillment-only"


def test_economic_negatives_small_when_full_data(cm):
    """On full data, economic negatives should be a small $ amount vs net sales."""
    if len(cm) < 1000:
        pytest.skip("sample mode")
    nf = (cm["n_order_lines"] == 0) & (cm["n_canceled_lines"] > 0)
    econ_neg = cm[(cm["customer_contribution"] < 0) & ~nf]
    net = cm["net_sales"].sum()
    exposure = abs(econ_neg["customer_contribution"].sum()) / max(net, 1)
    assert exposure < 0.005, f"economic neg exposure {exposure:.4%} of net sales"


def test_honest_summary_if_present():
    path = OUTPUTS / "honest_economics_summary.json"
    if not path.exists():
        pytest.skip("run honest_economics first")
    import json
    with open(path) as f:
        s = json.load(f)
    assert s["cm"]["economic_negative"] + s["cm"]["non_fulfillment_only_negative"] == s["cm"]["baseline_negative"]
    assert abs(s["cm"]["economic_negative_total_brl"]) < 20_000
    v1 = s["orders_v1"]["negative"]
    pt = s.get("orders_passthrough", s.get("orders_net_freight", {})).get("negative", v1)
    assert pt <= v1


def test_tipping_summary_if_present():
    path = OUTPUTS / "freight_and_tipping_summary.json"
    if not path.exists():
        pytest.skip("run tipping_and_freight first")
    import json
    with open(path) as f:
        s = json.load(f)
    cases = {c["case"]: c for c in s["freight_cases"]}
    pt = cases["pass_through"]["negative_orders"]
    cheap = cases.get("modeled_pool_with_credit", cases.get("modeled_27pct_with_credit"))
    sub = cases["subsidized_150pct"]["negative_orders"]
    assert cheap is not None
    assert pt >= cheap["negative_orders"]
    assert sub >= pt
    assert "sales_exposed_pct" in cases["pass_through"]
