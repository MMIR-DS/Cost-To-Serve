"""Smoke tests for dashboard inputs from shipped JSON/CSV (no Streamlit runtime required)."""
from pathlib import Path
import json
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"


def test_freight_sales_exposed_is_percent_points_not_fraction():
    path = OUTPUTS / "freight_and_tipping_summary.json"
    if not path.exists():
        pytest.skip("freight summary missing")
    data = json.loads(path.read_text())
    cases = {c["case"]: c for c in data["freight_cases"]}
    assert "pass_through" in cases
    assert "V1_no_credit_modeled_pool" in cases
    pt = cases["pass_through"]
    assert 0.01 < pt["sales_exposed_pct"] < 0.1
    display = f"{pt['sales_exposed_pct']:.3f}%"
    assert display.startswith("0.027")
    assert float(display.replace("%", "")) < 1.0


def test_freight_case_lookup_needles():
    path = OUTPUTS / "freight_and_tipping_summary.json"
    if not path.exists():
        pytest.skip("freight summary missing")
    cases = json.loads(path.read_text())["freight_cases"]

    def find(*needles):
        for x in cases:
            key = str(x.get("case", "")).lower()
            if any(n.lower() in key for n in needles):
                return x
        return None

    pt = find("pass_through")
    v1 = find("v1", "no_credit")
    assert pt is not None and pt["negative_orders"] == 101
    assert v1 is not None and v1["negative_orders"] == 1029


def test_tipping_grid_wide_heatmap_matrix_finite():
    path = OUTPUTS / "tipping_grid_passthrough.csv"
    if not path.exists():
        pytest.skip("tipping grid missing")
    g = pd.read_csv(path)
    sales_cols = [c for c in g.columns if str(c).startswith("sales_exposed_pct_")]
    assert "cogs_pct" in g.columns
    assert len(sales_cols) >= 3
    z = g[sales_cols].apply(pd.to_numeric, errors="coerce")
    assert z.notna().all().all()
    assert "sales_exposed_pct_1.0" in g.columns
    row = g.loc[(g["cogs_pct"] - 0.35).abs().idxmin()]
    assert 0.01 < float(row["sales_exposed_pct_1.0"]) < 0.1
