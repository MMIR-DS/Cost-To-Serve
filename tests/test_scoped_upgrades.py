import json
from pathlib import Path
import pytest

OUTPUTS = Path(__file__).resolve().parents[1] / "outputs"
PROCESSED = Path(__file__).resolve().parents[1] / "data" / "processed"


def test_monte_carlo_summary_shape():
    path = OUTPUTS / "monte_carlo_summary.json"
    if not path.exists():
        pytest.skip("run monte_carlo_sensitivity first")
    d = json.loads(path.read_text())
    if d.get("status") == "skipped_insufficient_rows":
        pytest.skip("full CTS not present — MC correctly skipped")
    assert d["n_draws"] >= 50
    p50 = d["economic_negative_cm_count"]["pctile_50_of_simulation"]
    p95 = d["economic_negative_cm_count"]["pctile_95_of_simulation"]
    assert 100 <= p50 <= 160
    assert 180 <= p95 <= 320
    assert d["share_economic_cm_negative"]["pctile_95_of_simulation"] < 0.01
    base = d["baseline_point_compare"]["neutral_freight_neg_cm_at_defaults"]
    assert base > 0
    ratio = d["baseline_point_compare"]["median_over_baseline"]
    assert 1.05 <= ratio <= 1.40
    rs = d["returns_pool_stress"]
    assert rs["x0.5"]["economic_negative_cm"] <= rs["x1.0"]["economic_negative_cm"]
    assert rs["x1.0"]["economic_negative_cm"] <= rs["x2.0"]["economic_negative_cm"]
    assert rs["x1.0"]["economic_negative_cm"] == base
    assert 1.05 <= d["baseline_point_compare"]["median_over_baseline"] <= 1.40
    assert d["baseline_point_compare"]["p95_over_baseline"] >= d["baseline_point_compare"]["median_over_baseline"]


def test_impact_effort_positive_only_and_risks_separated():
    path = OUTPUTS / "impact_effort.json"
    if not path.exists():
        pytest.skip("run impact_effort first")
    d = json.loads(path.read_text())
    assert "positive_levers" in d and "risk_or_pressure" in d
    assert "recommended_read_order" not in d
    assert "priority_index" not in json.dumps(d)
    for r in d["positive_levers"]:
        assert r["delta_customer_contribution_brl"] > 0
    for r in d["risk_or_pressure"]:
        assert r["delta_customer_contribution_brl"] <= 0
    pos_names = {r["scenario"] for r in d["positive_levers"]}
    assert "price_down_pressure" not in pos_names
    assert "premium_service" not in pos_names


def test_industry_context_doc_exists():
    assert (Path(__file__).resolve().parents[1] / "docs" / "industry_context.md").exists()
