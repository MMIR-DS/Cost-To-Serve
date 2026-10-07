"""Cross-checks on tipping grids and economic robust classes."""
import pytest
import pandas as pd
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def test_v1_grid_matches_freight_summary():
    grid_path = OUTPUTS / "tipping_grid_v1.csv"
    freight_path = OUTPUTS / "freight_and_tipping_summary.json"
    if not grid_path.exists() or not freight_path.exists():
        pytest.skip("run tipping_and_freight first")
    grid = pd.read_csv(grid_path)
    with open(freight_path) as f:
        freight = json.load(f)
    row = grid[grid["cogs_pct"] == 0.35].iloc[0]
    pct = float(row["neg_order_pct_1.0"])
    v1 = next(c for c in freight["freight_cases"] if "V1" in c["case"] or "no_credit" in c["case"])
    assert abs(pct - v1["negative_pct_orders"]) < 1e-6


def test_passthrough_fewer_negatives_than_v1():
    path = OUTPUTS / "freight_and_tipping_summary.json"
    if not path.exists():
        pytest.skip("missing summary")
    with open(path) as f:
        s = json.load(f)
    cases = {c["case"]: c for c in s["freight_cases"]}
    pt = cases["pass_through"]["negative_orders"]
    v1 = next(c for c in s["freight_cases"] if "V1" in c["case"] or "no_credit" in c["case"])
    assert pt < v1["negative_orders"]
    if "sales_exposed_pct" in cases["pass_through"]:
        assert cases["pass_through"]["sales_exposed_pct"] < v1["sales_exposed_pct"]


def test_sales_exposed_columns_exist():
    path = OUTPUTS / "tipping_grid_v1.csv"
    if not path.exists():
        pytest.skip("missing grid")
    df = pd.read_csv(path)
    assert any(c.startswith("sales_exposed") for c in df.columns)


def test_economic_robust_pass_through_reference():
    path = OUTPUTS / "economic_robust_classes.json"
    if not path.exists():
        pytest.skip("run economic_robustness first")
    with open(path) as f:
        s = json.load(f)
    assert s.get("cost_structure") == "pass_through_freight_reference"
    assert "pt_best_corner" in s["scenarios_used"]
    assert "pt_worst_corner" in s["scenarios_used"]
    assert "pt_oh_on_orders" in s["scenarios_used"]
    assert s["robust_negative"] < 30
    assert s["baseline_negative_pass_through"] <= s["baseline_negative_v1_sensitivity"]


def test_returns_mixed_allocation_matches_rate_times_lines():
    path = OUTPUTS / "economic_robust_classes.json"
    if not path.exists():
        pytest.skip("run economic_robustness first")
    d = json.load(open(path))
    if "mixed_canceled_lines" not in d:
        pytest.skip("field not present")
    expected = d["returns_per_canceled_line"] * d["mixed_canceled_lines"]
    assert abs(d["returns_allocated_to_mixed_months_brl"] - expected) < 1.0
